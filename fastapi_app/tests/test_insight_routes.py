from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.routes.insights import get_services, router
from app.composition import build_application_services
from app.config import FASTAPI_ROOT
from app.database import Base
from app.domain.learning_evidence.entities import Skill
from app.domain.study_plan.entities import StudyPlanItemStatus
from app.models.learning_evidence import LearningResource, StudySession


def test_history_and_progress_render_persisted_plan_and_session_data() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        _add_resources(session)
        services = build_application_services(session)
        today = datetime.now(ZoneInfo("Australia/Sydney")).date()
        plan = services.study_plan.get_or_create_daily_plan("local-user", today)
        services.study_plan.update_item_status(
            "local-user",
            today,
            plan.items[0].id,
            StudyPlanItemStatus.COMPLETED,
        )
        session.add(
            StudySession(
                user_key="local-user",
                resource_id=plan.items[0].resource_id,
                skill=Skill.LISTENING.value,
                source_type="route-test",
                source_id="attempt-1",
                source_revision=1,
                status="completed",
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                actual_duration_seconds=600,
                accuracy=0.75,
                attempt_count=1,
                incorrect_item_count=2,
                notes="",
            )
        )
        session.commit()
        summary = services.progress_analytics.get_summary("local-user", today)

        assert summary.current_streak == 1
        assert summary.longest_streak == 1
        assert summary.total_study_days == 1
        assert summary.completed_planned_minutes == 30
        assert summary.tracked_seconds == 600

        app = FastAPI()
        app.mount(
            "/static",
            StaticFiles(directory=FASTAPI_ROOT / "app" / "static"),
            name="static",
        )
        app.include_router(router)
        app.dependency_overrides[get_services] = lambda: services

        with TestClient(app) as client:
            history = client.get("/history")
            calendar = client.get(
                f"/history?view=calendar&month={today.strftime('%Y-%m')}"
            )
            detail = client.get(f"/history/{today.isoformat()}")
            progress = client.get("/progress")

        assert history.status_code == 200
        assert "你的学习记录，没有消失" in history.text
        assert "1/4 模块完成" in history.text
        assert calendar.status_code == 200
        assert "calendar-grid" in calendar.text
        assert detail.status_code == 200
        assert "75%" in detail.text
        assert "10 min" in detail.text
        assert progress.status_code == 200
        assert "看清坚持，也看清证据" in progress.text
        assert "25.0%" in progress.text
        assert "10m" in progress.text


def test_history_rejects_invalid_month_and_missing_day() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        services = build_application_services(session)
        app = FastAPI()
        app.mount(
            "/static",
            StaticFiles(directory=FASTAPI_ROOT / "app" / "static"),
            name="static",
        )
        app.include_router(router)
        app.dependency_overrides[get_services] = lambda: services

        with TestClient(app) as client:
            invalid = client.get("/history?view=calendar&month=September")
            missing = client.get("/history/2020-01-01")

        assert invalid.status_code == 422
        assert missing.status_code == 404


def _add_resources(session: Session) -> None:
    session.add_all(
        [
            LearningResource(
                slug=f"{skill.value}-history-resource",
                title=f"{skill.value.title()} history resource",
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
        ]
    )
    session.commit()
