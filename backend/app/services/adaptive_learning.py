from collections.abc import Callable
from datetime import date, datetime, timezone

from app.domain.adaptive_learning.entities import (
    AIPlanItemRecommendation,
    AIPlanItemRecommendationResponse,
    AIRecommendationAction,
    AdaptationDecision,
    AdaptationDecisionType,
    ManualPlanItemOverride,
)
from app.domain.adaptive_learning.repository import AdaptationDecisionRepository
from app.domain.learning_evidence.entities import Skill
from app.domain.study_plan.config import SKILL_TIME_CONFIG
from app.domain.study_plan.entities import DailyStudyPlan, StudyPlanItemStatus
from app.domain.study_plan.repository import StudyPlanRepository
from app.services.resources import ResourceService


class AdaptationDecisionService:
    def __init__(
        self,
        study_plan_repository: StudyPlanRepository,
        decision_repository: AdaptationDecisionRepository,
        resource_service: ResourceService,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.study_plan_repository = study_plan_repository
        self.decision_repository = decision_repository
        self.resource_service = resource_service
        self.now = now or utc_now

    def override_plan_item(
        self,
        user_key: str,
        plan_date: date,
        study_plan_item_id: int,
        *,
        planned_minutes: int,
        resource_id: int | None,
        note: str = "",
    ) -> DailyStudyPlan:
        plan = self.study_plan_repository.get_for_date(user_key, plan_date)
        if plan is None:
            raise LookupError("Study plan not found")
        item = next(
            (value for value in plan.items if value.id == study_plan_item_id),
            None,
        )
        if item is None:
            raise LookupError("Study plan item not found")
        time_config = SKILL_TIME_CONFIG[item.skill]
        if not time_config.minimum_minutes <= planned_minutes <= time_config.maximum_minutes:
            raise InvalidPlanOverrideError(
                f"{item.skill.value} duration must be between "
                f"{time_config.minimum_minutes} and {time_config.maximum_minutes} minutes"
            )
        if resource_id is not None:
            resource = self.resource_service.get_resource(resource_id)
            if resource is None or not resource.active:
                raise InvalidPlanOverrideError("Replacement resource is unavailable")
            if resource.skill is not item.skill:
                raise InvalidPlanOverrideError(
                    "Replacement resource must match the study-plan skill"
                )
        if planned_minutes == item.planned_minutes and resource_id == item.resource_id:
            return plan

        updated_total = plan.total_minutes - item.planned_minutes + planned_minutes
        remains_overridden = (
            planned_minutes != item.system_planned_minutes
            or resource_id != item.system_resource_id
        )
        self.decision_repository.apply_manual_override(
            ManualPlanItemOverride(
                study_plan_id=plan.id,
                study_plan_item_id=item.id,
                skill=item.skill,
                previous_planned_minutes=item.planned_minutes,
                new_planned_minutes=planned_minutes,
                previous_resource_id=item.resource_id,
                new_resource_id=resource_id,
                updated_plan_total_minutes=updated_total,
                remains_overridden=remains_overridden,
                note=note.strip(),
                decided_at=self.now(),
            )
        )
        updated = self.study_plan_repository.get_for_date(user_key, plan_date)
        if updated is None:
            raise RuntimeError("Study plan disappeared after override")
        return updated

    def get_plan_decisions(self, study_plan_id: int) -> tuple[AdaptationDecision, ...]:
        return self.decision_repository.list_for_plan(study_plan_id)

    def get_pending_ai_recommendations(
        self,
        user_key: str,
        plan_date: date,
    ) -> tuple[AdaptationDecision, ...]:
        plan = self.study_plan_repository.get_for_date(user_key, plan_date)
        if plan is None:
            return ()
        pending_by_item: dict[int, AdaptationDecision] = {}
        for decision in self.decision_repository.list_for_plan(plan.id):
            if decision.decision_type is AdaptationDecisionType.AI_RECOMMENDATION:
                pending_by_item[decision.study_plan_item_id] = decision
                continue
            if (
                decision.decision_type
                in {
                    AdaptationDecisionType.AI_RECOMMENDATION_ACCEPTED,
                    AdaptationDecisionType.AI_RECOMMENDATION_DISMISSED,
                }
                and decision.source_decision_id is not None
            ):
                pending = pending_by_item.get(decision.study_plan_item_id)
                if pending is not None and pending.id == decision.source_decision_id:
                    pending_by_item.pop(decision.study_plan_item_id)
        return tuple(
            pending_by_item[item.id]
            for item in plan.items
            if item.id in pending_by_item
        )

    def save_ai_recommendation(
        self,
        user_key: str,
        plan_date: date,
        study_plan_item_id: int,
        *,
        proposed_minutes: int,
        proposed_resource_id: int | None,
        reasons: tuple[str, ...],
        provider_name: str,
        model_name: str,
    ) -> AdaptationDecision:
        plan = self.study_plan_repository.get_for_date(user_key, plan_date)
        if plan is None:
            raise LookupError("Study plan not found")
        item = next(
            (value for value in plan.items if value.id == study_plan_item_id),
            None,
        )
        if item is None:
            raise LookupError("Study plan item not found")
        time_config = SKILL_TIME_CONFIG[item.skill]
        if not time_config.minimum_minutes <= proposed_minutes <= time_config.maximum_minutes:
            raise InvalidPlanOverrideError(
                f"{item.skill.value} duration must be between "
                f"{time_config.minimum_minutes} and {time_config.maximum_minutes} minutes"
            )
        if proposed_resource_id is not None:
            resource = self.resource_service.get_resource(proposed_resource_id)
            if resource is None or not resource.active:
                raise InvalidPlanOverrideError("Recommended resource is unavailable")
            if resource.skill is not item.skill:
                raise InvalidPlanOverrideError(
                    "Recommended resource must match the study-plan skill"
                )
        normalized_reasons = tuple(value.strip() for value in reasons if value.strip())
        if not normalized_reasons:
            raise InvalidPlanOverrideError("AI recommendation requires measured reasons")
        normalized_provider = provider_name.strip()
        normalized_model = model_name.strip()
        if not normalized_provider or not normalized_model:
            raise InvalidPlanOverrideError(
                "AI recommendation requires provider and model identifiers"
            )
        if (
            proposed_minutes == item.planned_minutes
            and proposed_resource_id == item.resource_id
        ):
            raise InvalidPlanOverrideError(
                "AI recommendation must propose a plan change"
            )
        return self.decision_repository.append_ai_recommendation(
            AIPlanItemRecommendation(
                study_plan_id=plan.id,
                study_plan_item_id=item.id,
                skill=item.skill,
                current_planned_minutes=item.planned_minutes,
                proposed_planned_minutes=proposed_minutes,
                current_resource_id=item.resource_id,
                proposed_resource_id=proposed_resource_id,
                reasons=normalized_reasons,
                provider_name=normalized_provider,
                model_name=normalized_model,
                decided_at=self.now(),
            )
        )

    def respond_to_ai_recommendation(
        self,
        user_key: str,
        plan_date: date,
        recommendation_id: int,
        *,
        action: AIRecommendationAction,
        note: str = "",
    ) -> DailyStudyPlan:
        plan = self.study_plan_repository.get_for_date(user_key, plan_date)
        if plan is None:
            raise LookupError("Study plan not found")
        recommendation = next(
            (
                decision
                for decision in self.get_pending_ai_recommendations(
                    user_key, plan_date
                )
                if decision.id == recommendation_id
            ),
            None,
        )
        if recommendation is None:
            raise LookupError("Pending AI recommendation not found")
        item = next(
            (
                value
                for value in plan.items
                if value.id == recommendation.study_plan_item_id
            ),
            None,
        )
        if item is None:
            raise LookupError("Study plan item not found")
        if (
            action is AIRecommendationAction.ACCEPT
            and item.status is StudyPlanItemStatus.COMPLETED
        ):
            raise InvalidPlanOverrideError(
                "Completed study-plan items cannot apply AI recommendations"
            )
        if (
            action is AIRecommendationAction.ACCEPT
            and (
                item.planned_minutes != recommendation.previous_planned_minutes
                or item.resource_id != recommendation.previous_resource_id
            )
        ):
            raise StaleAIRecommendationError(
                "The study plan changed after this AI recommendation was saved"
            )
        if action is AIRecommendationAction.ACCEPT:
            self._validate_ai_recommendation_target(item.skill, recommendation)
        new_total = (
            plan.total_minutes
            - item.planned_minutes
            + recommendation.new_planned_minutes
            if action is AIRecommendationAction.ACCEPT
            else plan.total_minutes
        )
        remains_overridden = (
            recommendation.new_planned_minutes != item.system_planned_minutes
            or recommendation.new_resource_id != item.system_resource_id
        )
        response_note = note.strip() or (
            f"已接受 AI 建议 #{recommendation.id}"
            if action is AIRecommendationAction.ACCEPT
            else f"已忽略 AI 建议 #{recommendation.id}"
        )
        self.decision_repository.respond_to_ai_recommendation(
            AIPlanItemRecommendationResponse(
                recommendation_id=recommendation.id,
                study_plan_id=plan.id,
                study_plan_item_id=item.id,
                skill=item.skill,
                action=action,
                current_planned_minutes=item.planned_minutes,
                proposed_planned_minutes=recommendation.new_planned_minutes,
                current_resource_id=item.resource_id,
                proposed_resource_id=recommendation.new_resource_id,
                updated_plan_total_minutes=new_total,
                remains_overridden=remains_overridden,
                note=response_note,
                decided_at=self.now(),
            )
        )
        updated = self.study_plan_repository.get_for_date(user_key, plan_date)
        if updated is None:
            raise RuntimeError("Study plan disappeared after AI recommendation response")
        return updated

    def _validate_ai_recommendation_target(
        self,
        skill: Skill,
        recommendation: AdaptationDecision,
    ) -> None:
        time_config = SKILL_TIME_CONFIG[skill]
        if not (
            time_config.minimum_minutes
            <= recommendation.new_planned_minutes
            <= time_config.maximum_minutes
        ):
            raise InvalidPlanOverrideError(
                "Saved AI recommendation duration is no longer valid"
            )
        if recommendation.new_resource_id is None:
            return
        resource = self.resource_service.get_resource(
            recommendation.new_resource_id
        )
        if resource is None or not resource.active or resource.skill is not skill:
            raise InvalidPlanOverrideError(
                "Saved AI recommendation resource is no longer available"
            )


class InvalidPlanOverrideError(ValueError):
    pass


class StaleAIRecommendationError(RuntimeError):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
