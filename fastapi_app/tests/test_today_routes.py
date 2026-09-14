from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.routes.today import get_services, router
from app.composition import build_application_services
from app.config import FASTAPI_ROOT
from app.database import Base
from app.domain.learning_evidence.entities import Skill
from app.models.learning_evidence import LearningResource


def test_today_page_and_typed_plan_actions_use_the_same_services() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        _add_resources(session)
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
            page = client.get("/today")

            assert page.status_code == 200
            assert "TODAY'S STUDY PLAN" in page.text
            assert "精听 Listening" in page.text
            assert "跟读与复述 Speaking" in page.text
            assert "阅读 Reading" in page.text
            assert "词块与复习 Vocabulary" in page.text
            assert "ACTIVE STUDY TIME" in page.text

            plan_date = datetime.now(ZoneInfo("Australia/Sydney")).date()
            plan = services.study_plan.get_daily_plan("local-user", plan_date)
            listening = plan.items[0]
            replacement = session.scalar(
                select(LearningResource).where(
                    LearningResource.skill == Skill.LISTENING.value,
                    LearningResource.id != listening.resource_id,
                )
            )
            override = client.put(
                f"/api/study-plans/{plan_date}/items/{listening.id}",
                json={
                    "planned_minutes": 35,
                    "resource_id": replacement.id,
                    "note": "Route test",
                },
            )

            assert override.status_code == 200
            assert override.json()["total_minutes"] == 115
            assert override.json()["items"][0]["manual_override"] is True

            started = client.post(
                f"/api/study-plans/{plan_date}/items/{listening.id}/sessions"
            )
            assert started.status_code == 200
            assert started.json()["status"] == "in_progress"

            saved = client.patch(
                f"/api/study-plans/{plan_date}/items/{listening.id}/sessions/"
                f"{started.json()['id']}",
                json={
                    "active_duration_seconds": 75,
                    "notes": "Route test note",
                    "perceived_difficulty": 4,
                    "confidence": 3,
                },
            )
            assert saved.status_code == 200
            assert saved.json()["active_duration_seconds"] == 75

            completed = client.post(
                f"/api/study-plans/{plan_date}/items/{listening.id}/sessions/"
                f"{started.json()['id']}/complete",
                json={
                    "active_duration_seconds": 90,
                    "notes": "Finished",
                    "perceived_difficulty": 4,
                    "confidence": 3,
                },
            )

            assert completed.status_code == 200
            assert completed.json()["status"] == "completed"
            finished_plan = services.study_plan.get_daily_plan("local-user", plan_date)
            assert finished_plan is not None
            assert finished_plan.items[0].status.value == "completed"


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
