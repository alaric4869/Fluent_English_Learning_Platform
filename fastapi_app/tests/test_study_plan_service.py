from datetime import date, datetime, timezone

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.database import Base
from app.domain.learning_evidence.entities import Skill
from app.domain.learner_profile.rule_based_evaluator import RuleBasedSkillEvaluator
from app.domain.resources.rule_based_recommender import RuleBasedResourceRecommender
from app.domain.study_plan.rule_based_generator import RuleBasedStudyPlanGenerator
from app.domain.study_plan.entities import StudyPlanItemStatus, StudyPlanStatus
from app.domain.weakness_detection.rule_based_detector import RuleBasedWeaknessDetector
from app.models.learning_evidence import LearningResource
from app.models.study_plan import StudyPlanItemModel, StudyPlanModel
from app.repositories.sqlalchemy_learning_evidence import SqlAlchemyLearningEvidenceRepository
from app.repositories.sqlalchemy_learner_profile import SqlAlchemyLearnerProfileRepository
from app.repositories.sqlalchemy_resources import SqlAlchemyResourceRepository
from app.repositories.sqlalchemy_study_plan import SqlAlchemyStudyPlanRepository
from app.repositories.sqlalchemy_weakness_detection import (
    SqlAlchemyWeaknessAssessmentRepository,
)
from app.services.learning_evidence import LearningEvidenceService
from app.services.learner_profile import LearnerProfileService
from app.services.resources import ResourceService
from app.services.study_plan import StudyPlanService
from app.services.weakness_detection import WeaknessDetectionService


PLAN_DATE = date(2026, 9, 14)
OCCURRED_AT = datetime(2026, 9, 14, 10, 30, tzinfo=timezone.utc)


def test_daily_plan_is_persisted_once_with_four_independent_items() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        _add_resources(session)
        service = _service(session)

        first = service.get_or_create_daily_plan("learner", PLAN_DATE)
        repeated = service.get_or_create_daily_plan("learner", PLAN_DATE)

        assert first.created is True
        assert repeated.created is False
        assert repeated.id == first.id
        assert first.total_minutes == 110
        assert [item.skill for item in first.items] == list(Skill)
        assert all(item.resource_id is not None for item in first.items)
        assert all(item.system_resource_id == item.resource_id for item in first.items)
        assert all(item.system_planned_minutes == item.planned_minutes for item in first.items)
        assert all(item.manual_override is False for item in first.items)
        assert _count(session, StudyPlanModel) == 1
        assert _count(session, StudyPlanItemModel) == 4


def test_missing_resource_does_not_create_fake_content() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        service = _service(session)

        plan = service.get_or_create_daily_plan("learner", PLAN_DATE)

        assert all(item.resource_id is None for item in plan.items)
        assert all(any("没有可用" in reason for reason in item.reasons) for item in plan.items)


def test_next_date_rotates_resources_that_were_already_assigned() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        _add_resources(session, resources_per_skill=2)
        service = _service(session)

        first = service.get_or_create_daily_plan("learner", PLAN_DATE)
        second = service.get_or_create_daily_plan(
            "learner",
            date(2026, 9, 15),
        )

        assert [item.resource_id for item in first.items] != [
            item.resource_id for item in second.items
        ]
        assert all(
            before.resource_id != after.resource_id
            for before, after in zip(first.items, second.items, strict=True)
        )


def test_plan_is_complete_only_after_every_module_is_complete() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        _add_resources(session)
        service = _service(session, now=lambda: OCCURRED_AT)
        plan = service.get_or_create_daily_plan("learner", PLAN_DATE)

        for item in plan.items[:-1]:
            plan = service.update_item_status(
                "learner",
                PLAN_DATE,
                item.id,
                StudyPlanItemStatus.COMPLETED,
            )
            assert plan.status is StudyPlanStatus.ACTIVE
        plan = service.update_item_status(
            "learner",
            PLAN_DATE,
            plan.items[-1].id,
            StudyPlanItemStatus.COMPLETED,
        )

        assert plan.status is StudyPlanStatus.COMPLETED
        assert all(item.status is StudyPlanItemStatus.COMPLETED for item in plan.items)
        assert all(item.started_at == OCCURRED_AT for item in plan.items)
        assert all(item.completed_at == OCCURRED_AT for item in plan.items)

        reopened = service.update_item_status(
            "learner",
            PLAN_DATE,
            plan.items[0].id,
            StudyPlanItemStatus.PENDING,
        )

        assert reopened.status is StudyPlanStatus.ACTIVE
        assert reopened.items[0].started_at == OCCURRED_AT
        assert reopened.items[0].completed_at is None


def test_start_time_is_preserved_across_status_changes() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    first_start = datetime(2026, 9, 14, 9, 0, tzinfo=timezone.utc)
    completed_at = datetime(2026, 9, 14, 9, 30, tzinfo=timezone.utc)
    current_time = first_start
    with Session(engine, expire_on_commit=False) as session:
        _add_resources(session)
        service = _service(session, now=lambda: current_time)
        plan = service.get_or_create_daily_plan("learner", PLAN_DATE)
        item_id = plan.items[0].id

        plan = service.update_item_status(
            "learner",
            PLAN_DATE,
            item_id,
            StudyPlanItemStatus.IN_PROGRESS,
        )
        assert plan.items[0].started_at == first_start
        assert plan.items[0].completed_at is None

        current_time = completed_at
        plan = service.update_item_status(
            "learner",
            PLAN_DATE,
            item_id,
            StudyPlanItemStatus.COMPLETED,
        )
        assert plan.items[0].started_at == first_start
        assert plan.items[0].completed_at == completed_at


def _service(session: Session, now=None) -> StudyPlanService:
    evidence_service = LearningEvidenceService(SqlAlchemyLearningEvidenceRepository(session))
    profile_service = LearnerProfileService(
        evidence_service,
        SqlAlchemyLearnerProfileRepository(session),
        RuleBasedSkillEvaluator(),
    )
    weakness_service = WeaknessDetectionService(
        profile_service,
        SqlAlchemyWeaknessAssessmentRepository(session),
        RuleBasedWeaknessDetector(),
    )
    resource_service = ResourceService(
        SqlAlchemyResourceRepository(session),
        RuleBasedResourceRecommender(),
    )
    return StudyPlanService(
        SqlAlchemyStudyPlanRepository(session),
        weakness_service,
        resource_service,
        RuleBasedStudyPlanGenerator(),
        now=now,
    )


def _add_resources(session: Session, resources_per_skill: int = 1) -> None:
    session.add_all(
        [
            LearningResource(
                slug=f"{skill.value}-resource-{index}",
                title=f"{skill.value.title()} resource {index}",
                resource_type="practice",
                skill=skill.value,
                topic="Daily English",
                difficulty="intermediate",
                estimated_duration_minutes=30,
                content={},
                tags=[],
                priority=50,
                active=True,
            )
            for skill in Skill
            for index in range(1, resources_per_skill + 1)
        ]
    )
    session.commit()


def _count(session: Session, model) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0
