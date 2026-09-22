from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.adaptive_learning.entities import (
    AIPlanItemRecommendation,
    AIPlanItemRecommendationResponse,
    AIRecommendationAction,
    AdaptationActor,
    AdaptationDecision,
    AdaptationDecisionType,
    ManualPlanItemOverride,
)
from app.domain.adaptive_learning.repository import (
    AIRecommendationAlreadyRespondedError,
    StaleStudyPlanOverrideError,
)
from app.domain.learning_evidence.entities import Skill
from app.models.adaptive_learning import AdaptationDecisionModel
from app.models.study_plan import StudyPlanItemModel, StudyPlanModel


class SqlAlchemyAdaptationDecisionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def apply_manual_override(self, command: ManualPlanItemOverride) -> AdaptationDecision:
        statement = (
            select(StudyPlanItemModel)
            .where(
                StudyPlanItemModel.id == command.study_plan_item_id,
                StudyPlanItemModel.study_plan_id == command.study_plan_id,
            )
            .options(selectinload(StudyPlanItemModel.study_plan))
        )
        item = self.session.scalar(statement)
        if item is None:
            raise LookupError("Study plan item not found")
        if (
            item.planned_minutes != command.previous_planned_minutes
            or item.resource_id != command.previous_resource_id
        ):
            raise StaleStudyPlanOverrideError(
                "Study plan item changed before the override could be saved"
            )

        item.planned_minutes = command.new_planned_minutes
        item.resource_id = command.new_resource_id
        item.manual_override = command.remains_overridden
        item.override_note = command.note
        item.study_plan.total_minutes = command.updated_plan_total_minutes
        decision = AdaptationDecisionModel(
            study_plan_id=command.study_plan_id,
            study_plan_item_id=command.study_plan_item_id,
            decision_type=AdaptationDecisionType.MANUAL_OVERRIDE.value,
            actor=AdaptationActor.USER.value,
            skill=command.skill.value,
            previous_planned_minutes=command.previous_planned_minutes,
            new_planned_minutes=command.new_planned_minutes,
            previous_resource_id=command.previous_resource_id,
            new_resource_id=command.new_resource_id,
            reasons=_manual_override_reasons(command.note),
            created_at=command.decided_at,
        )
        self.session.add(decision)
        self.session.commit()
        self.session.refresh(decision)
        return self._to_decision(decision)

    def append_ai_recommendation(
        self,
        command: AIPlanItemRecommendation,
    ) -> AdaptationDecision:
        item = self.session.scalar(
            select(StudyPlanItemModel).where(
                StudyPlanItemModel.id == command.study_plan_item_id,
                StudyPlanItemModel.study_plan_id == command.study_plan_id,
            )
        )
        if item is None:
            raise LookupError("Study plan item not found")
        if (
            item.planned_minutes != command.current_planned_minutes
            or item.resource_id != command.current_resource_id
        ):
            raise StaleStudyPlanOverrideError(
                "Study plan item changed before the AI recommendation was saved"
            )
        reasons = [
            *command.reasons,
            f"AI provider: {command.provider_name}; model: {command.model_name}.",
            "This recommendation has not changed the learner's plan.",
        ]
        existing = self.session.scalar(
            select(AdaptationDecisionModel)
            .where(
                AdaptationDecisionModel.study_plan_id == command.study_plan_id,
                AdaptationDecisionModel.study_plan_item_id
                == command.study_plan_item_id,
                AdaptationDecisionModel.decision_type
                == AdaptationDecisionType.AI_RECOMMENDATION.value,
            )
            .order_by(AdaptationDecisionModel.id.desc())
        )
        if (
            existing is not None
            and existing.previous_planned_minutes == command.current_planned_minutes
            and existing.new_planned_minutes == command.proposed_planned_minutes
            and existing.previous_resource_id == command.current_resource_id
            and existing.new_resource_id == command.proposed_resource_id
            and existing.reasons == reasons
        ):
            return self._to_decision(existing)
        decision = AdaptationDecisionModel(
            study_plan_id=command.study_plan_id,
            study_plan_item_id=command.study_plan_item_id,
            decision_type=AdaptationDecisionType.AI_RECOMMENDATION.value,
            actor=AdaptationActor.AI.value,
            skill=command.skill.value,
            previous_planned_minutes=command.current_planned_minutes,
            new_planned_minutes=command.proposed_planned_minutes,
            previous_resource_id=command.current_resource_id,
            new_resource_id=command.proposed_resource_id,
            reasons=reasons,
            created_at=command.decided_at,
        )
        self.session.add(decision)
        self.session.commit()
        self.session.refresh(decision)
        return self._to_decision(decision)

    def respond_to_ai_recommendation(
        self,
        command: AIPlanItemRecommendationResponse,
    ) -> AdaptationDecision:
        recommendation = self.session.scalar(
            select(AdaptationDecisionModel).where(
                AdaptationDecisionModel.id == command.recommendation_id,
                AdaptationDecisionModel.study_plan_id == command.study_plan_id,
                AdaptationDecisionModel.study_plan_item_id
                == command.study_plan_item_id,
                AdaptationDecisionModel.decision_type
                == AdaptationDecisionType.AI_RECOMMENDATION.value,
            )
        )
        if recommendation is None:
            raise LookupError("AI recommendation not found")
        if (
            recommendation.skill != command.skill.value
            or recommendation.new_planned_minutes
            != command.proposed_planned_minutes
            or recommendation.new_resource_id != command.proposed_resource_id
        ):
            raise StaleStudyPlanOverrideError(
                "AI recommendation values no longer match the response command"
            )
        existing = self.session.scalar(
            select(AdaptationDecisionModel).where(
                AdaptationDecisionModel.source_decision_id
                == command.recommendation_id
            )
        )
        expected_type = (
            AdaptationDecisionType.AI_RECOMMENDATION_ACCEPTED
            if command.action is AIRecommendationAction.ACCEPT
            else AdaptationDecisionType.AI_RECOMMENDATION_DISMISSED
        )
        if existing is not None:
            if existing.decision_type == expected_type.value:
                return self._to_decision(existing)
            raise AIRecommendationAlreadyRespondedError(
                "AI recommendation already has a learner response"
            )

        item = self.session.scalar(
            select(StudyPlanItemModel)
            .where(
                StudyPlanItemModel.id == command.study_plan_item_id,
                StudyPlanItemModel.study_plan_id == command.study_plan_id,
            )
            .options(selectinload(StudyPlanItemModel.study_plan))
        )
        if item is None:
            raise LookupError("Study plan item not found")
        if (
            item.planned_minutes != command.current_planned_minutes
            or item.resource_id != command.current_resource_id
        ):
            raise StaleStudyPlanOverrideError(
                "Study plan item changed after the AI recommendation was saved"
            )

        accepted = command.action is AIRecommendationAction.ACCEPT
        new_minutes = (
            command.proposed_planned_minutes
            if accepted
            else command.current_planned_minutes
        )
        new_resource_id = (
            command.proposed_resource_id if accepted else command.current_resource_id
        )
        if accepted:
            item.planned_minutes = new_minutes
            item.resource_id = new_resource_id
            item.manual_override = command.remains_overridden
            item.override_note = command.note
            item.study_plan.total_minutes = command.updated_plan_total_minutes

        decision = AdaptationDecisionModel(
            study_plan_id=command.study_plan_id,
            study_plan_item_id=command.study_plan_item_id,
            source_decision_id=command.recommendation_id,
            decision_type=expected_type.value,
            actor=AdaptationActor.USER.value,
            skill=command.skill.value,
            previous_planned_minutes=command.current_planned_minutes,
            new_planned_minutes=new_minutes,
            previous_resource_id=command.current_resource_id,
            new_resource_id=new_resource_id,
            reasons=_ai_response_reasons(command),
            created_at=command.decided_at,
        )
        self.session.add(decision)
        self.session.commit()
        self.session.refresh(decision)
        return self._to_decision(decision)

    def list_for_plan(self, study_plan_id: int) -> tuple[AdaptationDecision, ...]:
        statement = (
            select(AdaptationDecisionModel)
            .where(AdaptationDecisionModel.study_plan_id == study_plan_id)
            # IDs preserve append order even when SQLite normalizes timezone-aware
            # timestamps differently from server-default timestamps.
            .order_by(AdaptationDecisionModel.id)
        )
        return tuple(self._to_decision(item) for item in self.session.scalars(statement))

    @staticmethod
    def _to_decision(item: AdaptationDecisionModel) -> AdaptationDecision:
        return AdaptationDecision(
            id=item.id,
            study_plan_id=item.study_plan_id,
            study_plan_item_id=item.study_plan_item_id,
            decision_type=AdaptationDecisionType(item.decision_type),
            actor=AdaptationActor(item.actor),
            skill=Skill(item.skill),
            previous_planned_minutes=item.previous_planned_minutes,
            new_planned_minutes=item.new_planned_minutes,
            previous_resource_id=item.previous_resource_id,
            new_resource_id=item.new_resource_id,
            reasons=tuple(item.reasons),
            created_at=item.created_at,
            source_decision_id=item.source_decision_id,
        )


def _manual_override_reasons(note: str) -> list[str]:
    reasons = ["用户手动覆盖了系统推荐。"]
    if note.strip():
        reasons.append(f"用户说明：{note.strip()}")
    return reasons


def _ai_response_reasons(
    command: AIPlanItemRecommendationResponse,
) -> list[str]:
    action = (
        "accepted"
        if command.action is AIRecommendationAction.ACCEPT
        else "dismissed"
    )
    reasons = [f"Learner {action} AI recommendation #{command.recommendation_id}."]
    if command.note.strip():
        reasons.append(f"Learner note: {command.note.strip()}")
    return reasons
