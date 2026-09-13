from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.learning_evidence.entities import Skill
from app.domain.study_plan.entities import (
    DailyStudyPlan,
    DailyStudyPlanItem,
    StudyPlanItemStatus,
    StudyPlanProposal,
    StudyPlanStatus,
)
from app.models.study_plan import StudyPlanItemModel, StudyPlanModel


class SqlAlchemyStudyPlanRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_for_date(self, user_key: str, plan_date: date) -> DailyStudyPlan | None:
        statement = (
            select(StudyPlanModel)
            .where(
                StudyPlanModel.user_key == user_key,
                StudyPlanModel.plan_date == plan_date,
            )
            .options(selectinload(StudyPlanModel.items))
        )
        plan = self.session.scalar(statement)
        return self._to_plan(plan, created=False) if plan else None

    def save(self, proposal: StudyPlanProposal) -> DailyStudyPlan:
        existing = self.get_for_date(proposal.user_key, proposal.plan_date)
        if existing is not None:
            return existing
        plan = StudyPlanModel(
            user_key=proposal.user_key,
            plan_date=proposal.plan_date,
            status=StudyPlanStatus.ACTIVE.value,
            source=proposal.source,
            generator_version=proposal.generator_version,
            weakness_assessment_run_id=proposal.weakness_assessment_run_id,
            recommender_version=proposal.recommender_version,
            total_minutes=proposal.total_minutes,
            explanation=list(proposal.explanation),
        )
        self.session.add(plan)
        self.session.flush()
        self.session.add_all(
            [
                StudyPlanItemModel(
                    study_plan_id=plan.id,
                    skill=item.skill.value,
                    position=item.position,
                    system_planned_minutes=item.planned_minutes,
                    planned_minutes=item.planned_minutes,
                    system_resource_id=item.resource_id,
                    resource_id=item.resource_id,
                    status=StudyPlanItemStatus.PENDING.value,
                    recommendation_score=item.recommendation_score,
                    reasons=list(item.reasons),
                    manual_override=False,
                    override_note="",
                )
                for item in proposal.items
            ]
        )
        self.session.commit()
        saved = self._get(plan.id)
        return self._to_plan(saved, created=True)

    def _get(self, plan_id: int) -> StudyPlanModel:
        statement = (
            select(StudyPlanModel)
            .where(StudyPlanModel.id == plan_id)
            .options(selectinload(StudyPlanModel.items))
        )
        return self.session.scalars(statement).one()

    @staticmethod
    def _to_plan(plan: StudyPlanModel, *, created: bool) -> DailyStudyPlan:
        items = tuple(
            DailyStudyPlanItem(
                id=item.id,
                skill=Skill(item.skill),
                position=item.position,
                system_planned_minutes=item.system_planned_minutes,
                planned_minutes=item.planned_minutes,
                system_resource_id=item.system_resource_id,
                resource_id=item.resource_id,
                status=StudyPlanItemStatus(item.status),
                recommendation_score=item.recommendation_score,
                reasons=tuple(item.reasons),
                manual_override=item.manual_override,
                override_note=item.override_note,
            )
            for item in sorted(plan.items, key=lambda value: value.position)
        )
        return DailyStudyPlan(
            id=plan.id,
            user_key=plan.user_key,
            plan_date=plan.plan_date,
            status=StudyPlanStatus(plan.status),
            source=plan.source,
            generator_version=plan.generator_version,
            weakness_assessment_run_id=plan.weakness_assessment_run_id,
            recommender_version=plan.recommender_version,
            total_minutes=plan.total_minutes,
            explanation=tuple(plan.explanation),
            items=items,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
            created=created,
        )
