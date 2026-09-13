from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.adaptive_learning.entities import (
    AdaptationActor,
    AdaptationDecision,
    AdaptationDecisionType,
    ManualPlanItemOverride,
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

    def list_for_plan(self, study_plan_id: int) -> tuple[AdaptationDecision, ...]:
        statement = (
            select(AdaptationDecisionModel)
            .where(AdaptationDecisionModel.study_plan_id == study_plan_id)
            .order_by(
                AdaptationDecisionModel.created_at,
                AdaptationDecisionModel.id,
            )
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
        )


class StaleStudyPlanOverrideError(RuntimeError):
    pass


def _manual_override_reasons(note: str) -> list[str]:
    reasons = ["用户手动覆盖了系统推荐。"]
    if note.strip():
        reasons.append(f"用户说明：{note.strip()}")
    return reasons
