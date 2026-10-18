from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.domain.adaptive_learning.entities import AdaptationActor, AdaptationDecisionType
from app.domain.learning_evidence.entities import Skill
from app.domain.study_plan.config import SKILL_TIME_CONFIG
from app.domain.study_plan.entities import (
    DailyStudyPlan,
    DailyStudyPlanItem,
    StudyPlanItemStatus,
    StudyPlanProposal,
    StudyPlanStatus,
)
from app.models.study_plan import StudyPlanItemModel, StudyPlanModel
from app.models.adaptive_learning import AdaptationDecisionModel


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

    def list_recent(
        self,
        user_key: str,
        through_date: date,
        limit: int,
    ) -> tuple[DailyStudyPlan, ...]:
        statement = (
            select(StudyPlanModel)
            .where(
                StudyPlanModel.user_key == user_key,
                StudyPlanModel.plan_date <= through_date,
            )
            .options(selectinload(StudyPlanModel.items))
            .order_by(StudyPlanModel.plan_date.desc(), StudyPlanModel.id.desc())
            .limit(limit)
        )
        return tuple(
            self._to_plan(plan, created=False)
            for plan in self.session.scalars(statement).unique()
        )

    def list_all_through(
        self,
        user_key: str,
        through_date: date,
    ) -> tuple[DailyStudyPlan, ...]:
        statement = (
            select(StudyPlanModel)
            .where(
                StudyPlanModel.user_key == user_key,
                StudyPlanModel.plan_date <= through_date,
            )
            .options(selectinload(StudyPlanModel.items))
            .order_by(StudyPlanModel.plan_date.desc(), StudyPlanModel.id.desc())
        )
        return tuple(
            self._to_plan(plan, created=False)
            for plan in self.session.scalars(statement).unique()
        )

    def list_between(
        self,
        user_key: str,
        start_date: date,
        end_date: date,
    ) -> tuple[DailyStudyPlan, ...]:
        statement = (
            select(StudyPlanModel)
            .where(
                StudyPlanModel.user_key == user_key,
                StudyPlanModel.plan_date >= start_date,
                StudyPlanModel.plan_date < end_date,
            )
            .options(selectinload(StudyPlanModel.items))
            .order_by(StudyPlanModel.plan_date.desc(), StudyPlanModel.id.desc())
        )
        return tuple(
            self._to_plan(plan, created=False)
            for plan in self.session.scalars(statement).unique()
        )

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
        try:
            self.session.flush()
        except IntegrityError:
            # Dashboard and Today may request the same missing date concurrently.
            # The database constraint is the final arbiter; after another request
            # wins the insert, return that committed plan instead of surfacing a
            # transient 500 to the React client.
            self.session.rollback()
            concurrent_plan = self.get_for_date(
                proposal.user_key,
                proposal.plan_date,
            )
            if concurrent_plan is not None:
                return concurrent_plan
            raise
        item_models = [
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
        self.session.add_all(item_models)
        self.session.flush()
        self.session.add_all(
            [
                AdaptationDecisionModel(
                    study_plan_id=plan.id,
                    study_plan_item_id=model.id,
                    decision_type=AdaptationDecisionType.SYSTEM_RECOMMENDATION.value,
                    actor=AdaptationActor.RULE_BASED.value,
                    skill=item.skill.value,
                    previous_planned_minutes=SKILL_TIME_CONFIG[
                        item.skill
                    ].default_minutes,
                    new_planned_minutes=item.planned_minutes,
                    previous_resource_id=None,
                    new_resource_id=item.resource_id,
                    reasons=list(item.reasons),
                )
                for item, model in zip(proposal.items, item_models, strict=True)
            ]
        )
        self.session.commit()
        saved = self._get(plan.id)
        return self._to_plan(saved, created=True)

    def set_item_status(
        self,
        user_key: str,
        plan_date: date,
        study_plan_item_id: int,
        status: StudyPlanItemStatus,
        plan_status: StudyPlanStatus,
        started_at: datetime | None,
        completed_at: datetime | None,
    ) -> DailyStudyPlan:
        statement = (
            select(StudyPlanModel)
            .where(
                StudyPlanModel.user_key == user_key,
                StudyPlanModel.plan_date == plan_date,
            )
            .options(selectinload(StudyPlanModel.items))
        )
        plan = self.session.scalar(statement)
        if plan is None:
            raise LookupError("Study plan not found")
        item = next(
            (value for value in plan.items if value.id == study_plan_item_id),
            None,
        )
        if item is None:
            raise LookupError("Study plan item not found")
        item.status = status.value
        item.started_at = started_at
        item.completed_at = completed_at
        plan.status = plan_status.value
        self.session.commit()
        saved = self._get(plan.id)
        return self._to_plan(saved, created=False)

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
                started_at=_as_utc(item.started_at),
                completed_at=_as_utc(item.completed_at),
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
            created_at=_as_utc(plan.created_at),
            updated_at=_as_utc(plan.updated_at),
            created=created,
        )


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
