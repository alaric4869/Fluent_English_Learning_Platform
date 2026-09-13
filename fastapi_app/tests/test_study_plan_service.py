from datetime import date

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.database import Base
from app.domain.learning_evidence.entities import Skill
from app.domain.learner_profile.rule_based_evaluator import RuleBasedSkillEvaluator
from app.domain.resources.rule_based_recommender import RuleBasedResourceRecommender
from app.domain.study_plan.rule_based_generator import RuleBasedStudyPlanGenerator
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


def _service(session: Session) -> StudyPlanService:
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
