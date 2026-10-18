from datetime import date, datetime, timezone

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.composition import build_application_services
from app.database import Base
from app.domain.learning_evidence.entities import Skill
from app.domain.study_plan.entities import StudyPlanItemStatus
from app.domain.study_session.entities import StudySessionProgress, StudySessionStatus
from app.models.learning_evidence import LearningResource, SkillPerformance, StudySession
from app.repositories.sqlalchemy_study_session import SqlAlchemyStudySessionRepository
from app.services.study_session import InvalidStudySessionError, StudySessionService


TODAY = date(2026, 9, 14)
NOW = datetime(2026, 9, 14, 8, 30, tzinfo=timezone.utc)


def test_module_session_persists_progress_and_subjective_profile_evidence() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    with Session(engine, expire_on_commit=False) as session:
        _add_resources(session)
        services = build_application_services(session)
        plan = services.study_plan.get_or_create_daily_plan("learner", TODAY)
        item = next(value for value in plan.items if value.skill is Skill.LISTENING)
        module_sessions = StudySessionService(
            SqlAlchemyStudySessionRepository(session),
            services.study_plan,
            services.learner_profile,
            services.weakness_detection,
            now=lambda: NOW,
        )

        started = module_sessions.start("learner", TODAY, item.id)

        assert started.status is StudySessionStatus.IN_PROGRESS
        assert started.revision == 1
        current_plan = services.study_plan.get_daily_plan("learner", TODAY)
        assert current_plan is not None
        assert current_plan.items[0].status is StudyPlanItemStatus.IN_PROGRESS
        replacement = session.scalar(
            select(LearningResource).where(
                LearningResource.skill == Skill.LISTENING.value,
                LearningResource.id != item.resource_id,
            )
        )
        assert replacement is not None
        with pytest.raises(InvalidStudySessionError):
            module_sessions.validate_resource_override(
                "learner", TODAY, item.id, replacement.id
            )

        first_save = module_sessions.save_progress(
            "learner",
            TODAY,
            item.id,
            started.id,
            StudySessionProgress(
                active_duration_seconds=120,
                notes="Could not hear the linking.",
                perceived_difficulty=4,
                confidence=3,
            ),
        )
        stale_save = module_sessions.save_progress(
            "learner",
            TODAY,
            item.id,
            started.id,
            StudySessionProgress(
                active_duration_seconds=90,
                notes="Updated note",
                perceived_difficulty=4,
                confidence=3,
            ),
        )

        assert first_save.active_duration_seconds == 120
        assert stale_save.active_duration_seconds == 120
        assert stale_save.notes == "Updated note"

        completed = module_sessions.complete(
            "learner",
            TODAY,
            item.id,
            started.id,
            StudySessionProgress(
                active_duration_seconds=180,
                notes="Final note",
                perceived_difficulty=4,
                confidence=3,
            ),
        )

        assert completed.status is StudySessionStatus.COMPLETED
        assert completed.active_duration_seconds == 180
        stored = session.get(StudySession, completed.id)
        assert stored is not None
        assert stored.accuracy is None
        performance = session.scalar(
            select(SkillPerformance).where(
                SkillPerformance.study_session_id == completed.id
            )
        )
        assert performance is not None
        assert performance.accuracy is None
        assert performance.metrics["evidence_type"] == "self_assessment"

        profile = services.learner_profile.get_current_profile("learner")
        assert profile is not None
        listening = next(value for value in profile.skills if value.skill is Skill.LISTENING)
        assert listening.score == 52.0
        assert listening.average_accuracy is None

        repeated = module_sessions.complete(
            "learner",
            TODAY,
            item.id,
            started.id,
            StudySessionProgress(
                active_duration_seconds=180,
                notes="Final note",
                perceived_difficulty=4,
                confidence=3,
            ),
        )
        assert repeated.id == completed.id
        assert session.scalar(select(func.count()).select_from(StudySession)) == 1
        assert session.scalar(select(func.count()).select_from(SkillPerformance)) == 1

        services.study_plan.update_item_status(
            "learner", TODAY, item.id, StudyPlanItemStatus.PENDING
        )
        restarted = module_sessions.start("learner", TODAY, item.id)
        assert restarted.revision == 2
        assert restarted.status is StudySessionStatus.IN_PROGRESS


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
                source_url=f"https://example.com/{skill.value}/{index}",
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
