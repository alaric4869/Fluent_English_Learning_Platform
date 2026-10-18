from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.domain.learning_evidence.entities import Skill
from app.models.learning_evidence import LearningResource, StudySession
from app.repositories.sqlalchemy_history import SqlAlchemyStudyHistoryRepository
from app.repositories.sqlalchemy_study_plan import SqlAlchemyStudyPlanRepository
from app.services.history import HistoryService


def test_sydney_day_includes_session_stored_on_previous_utc_date() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        resource = LearningResource(
            slug="boundary-listening",
            title="Sydney boundary listening",
            resource_type="practice",
            skill=Skill.LISTENING.value,
            topic="Daily English",
            difficulty="intermediate",
            estimated_duration_minutes=30,
            content={},
            tags=[],
            priority=50,
            active=True,
        )
        session.add(resource)
        session.flush()
        session.add(
            StudySession(
                user_key="learner",
                resource_id=resource.id,
                skill=Skill.LISTENING.value,
                source_type="timezone-test",
                source_id="session-1",
                source_revision=1,
                status="completed",
                started_at=datetime(2026, 9, 12, 14, 20, tzinfo=timezone.utc),
                completed_at=datetime(2026, 9, 12, 14, 30, tzinfo=timezone.utc),
                actual_duration_seconds=600,
                accuracy=0.8,
                attempt_count=1,
                incorrect_item_count=1,
                notes="",
            )
        )
        session.commit()
        service = HistoryService(
            SqlAlchemyStudyPlanRepository(session),
            SqlAlchemyStudyHistoryRepository(session),
            ZoneInfo("Australia/Sydney"),
        )

        day = service.get_day("learner", date(2026, 9, 13))

        assert day is not None
        assert len(day.sessions) == 1
        assert day.sessions[0].resource_title == "Sydney boundary listening"
