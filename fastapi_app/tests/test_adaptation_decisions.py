from datetime import date, datetime, timezone

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.database import Base
from app.domain.adaptive_learning.entities import (
    AdaptationActor,
    AdaptationDecisionType,
)
from app.domain.learning_evidence.entities import Skill
from app.domain.learner_profile.rule_based_evaluator import RuleBasedSkillEvaluator
from app.domain.resources.rule_based_recommender import RuleBasedResourceRecommender
from app.domain.study_plan.rule_based_generator import RuleBasedStudyPlanGenerator
from app.domain.weakness_detection.rule_based_detector import RuleBasedWeaknessDetector
from app.models.adaptive_learning import AdaptationDecisionModel
from app.models.learning_evidence import LearningResource
from app.repositories.sqlalchemy_adaptive_learning import (
    SqlAlchemyAdaptationDecisionRepository,
)
from app.repositories.sqlalchemy_learning_evidence import SqlAlchemyLearningEvidenceRepository
from app.repositories.sqlalchemy_learner_profile import SqlAlchemyLearnerProfileRepository
from app.repositories.sqlalchemy_resources import SqlAlchemyResourceRepository
from app.repositories.sqlalchemy_study_plan import SqlAlchemyStudyPlanRepository
from app.repositories.sqlalchemy_weakness_detection import (
    SqlAlchemyWeaknessAssessmentRepository,
)
from app.services.adaptive_learning import (
    AdaptationDecisionService,
    InvalidPlanOverrideError,
)
from app.services.learning_evidence import LearningEvidenceService
from app.services.learner_profile import LearnerProfileService
from app.services.resources import ResourceService
from app.services.study_plan import StudyPlanService
from app.services.weakness_detection import WeaknessDetectionService


PLAN_DATE = date(2026, 9, 14)
NOW = datetime(2026, 9, 13, 12, tzinfo=timezone.utc)


def test_manual_override_preserves_system_values_and_appends_audit_history() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        _add_resources(session)
        plan_service, decision_service = _services(session)
        plan = plan_service.get_or_create_daily_plan("learner", PLAN_DATE)
        listening = plan.items[0]
        replacement = session.scalar(
            select(LearningResource).where(
                LearningResource.skill == Skill.LISTENING.value,
                LearningResource.id != listening.resource_id,
            )
        )

        initial_decisions = decision_service.get_plan_decisions(plan.id)
        updated = decision_service.override_plan_item(
            "learner",
            PLAN_DATE,
            listening.id,
            planned_minutes=35,
            resource_id=replacement.id,
            note="今天想换一套听力",
        )

        assert len(initial_decisions) == 4
        assert all(
            item.decision_type is AdaptationDecisionType.SYSTEM_RECOMMENDATION
            for item in initial_decisions
        )
        changed = updated.items[0]
        assert changed.system_planned_minutes == 30
        assert changed.planned_minutes == 35
        assert changed.system_resource_id == listening.system_resource_id
        assert changed.resource_id == replacement.id
        assert changed.manual_override is True
        assert changed.override_note == "今天想换一套听力"
        assert updated.total_minutes == 115
        decisions = decision_service.get_plan_decisions(plan.id)
        assert len(decisions) == 5
        latest = decisions[-1]
        assert latest.decision_type is AdaptationDecisionType.MANUAL_OVERRIDE
        assert latest.actor is AdaptationActor.USER
        assert latest.previous_planned_minutes == 30
        assert latest.new_planned_minutes == 35
        assert latest.previous_resource_id == listening.resource_id
        assert latest.new_resource_id == replacement.id
        assert any("今天想换一套听力" in reason for reason in latest.reasons)

        unchanged = decision_service.override_plan_item(
            "learner",
            PLAN_DATE,
            listening.id,
            planned_minutes=35,
            resource_id=replacement.id,
            note="重复请求",
        )

        assert unchanged.total_minutes == 115
        assert _count(session, AdaptationDecisionModel) == 5

        reset = decision_service.override_plan_item(
            "learner",
            PLAN_DATE,
            listening.id,
            planned_minutes=listening.system_planned_minutes,
            resource_id=listening.system_resource_id,
            note="恢复系统推荐",
        )

        assert reset.items[0].manual_override is False
        assert reset.total_minutes == 110
        assert _count(session, AdaptationDecisionModel) == 6


def test_wrong_skill_resource_and_out_of_range_duration_are_rejected() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        _add_resources(session)
        plan_service, decision_service = _services(session)
        plan = plan_service.get_or_create_daily_plan("learner", PLAN_DATE)
        listening = plan.items[0]
        reading_resource = session.scalar(
            select(LearningResource).where(
                LearningResource.skill == Skill.READING.value
            )
        )

        with pytest.raises(InvalidPlanOverrideError, match="must match"):
            decision_service.override_plan_item(
                "learner",
                PLAN_DATE,
                listening.id,
                planned_minutes=30,
                resource_id=reading_resource.id,
            )
        with pytest.raises(InvalidPlanOverrideError, match="between 15 and 45"):
            decision_service.override_plan_item(
                "learner",
                PLAN_DATE,
                listening.id,
                planned_minutes=60,
                resource_id=listening.resource_id,
            )

        assert _count(session, AdaptationDecisionModel) == 4


def _services(session: Session) -> tuple[StudyPlanService, AdaptationDecisionService]:
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
    plan_repository = SqlAlchemyStudyPlanRepository(session)
    return (
        StudyPlanService(
            plan_repository,
            weakness_service,
            resource_service,
            RuleBasedStudyPlanGenerator(),
        ),
        AdaptationDecisionService(
            plan_repository,
            SqlAlchemyAdaptationDecisionRepository(session),
            resource_service,
            now=lambda: NOW,
        ),
    )


def _add_resources(session: Session) -> None:
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
            for index in range(1, 3 if skill is Skill.LISTENING else 2)
        ]
    )
    session.commit()


def _count(session: Session, model) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0
