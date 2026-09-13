from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.routes.review import get_services as get_review_services
from app.api.routes.review import router as review_router
from app.api.routes.insights import get_services as get_insight_services
from app.api.routes.insights import router as insights_router
from app.api.routes.today import get_services as get_today_services
from app.api.routes.today import router as today_router
from app.composition import build_application_services
from app.config import FASTAPI_ROOT
from app.database import Base
from app.domain.learning_evidence.entities import Skill
from app.models.learning_evidence import LearningResource


def test_review_page_create_rate_and_today_queue_share_persisted_state() -> None:
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
        app.include_router(today_router)
        app.include_router(review_router)
        app.include_router(insights_router)
        app.dependency_overrides[get_review_services] = lambda: services
        app.dependency_overrides[get_today_services] = lambda: services
        app.dependency_overrides[get_insight_services] = lambda: services
        today = datetime.now(ZoneInfo("Australia/Sydney")).date()

        with TestClient(app) as client:
            created = client.post(
                "/api/vocabulary",
                json={
                    "chunk": "make an appointment",
                    "meaning": "预约",
                    "example_sentence": "I need to make an appointment tomorrow.",
                    "learned_on": (today - timedelta(days=1)).isoformat(),
                    "difficulty": "medium",
                    "source_context": "Daily English",
                    "tags": ["appointments", "daily life"],
                },
            )
            duplicate = client.post(
                "/api/vocabulary",
                json={
                    "chunk": "  MAKE   AN APPOINTMENT ",
                    "meaning": "预约",
                    "learned_on": today.isoformat(),
                },
            )
            review_page = client.get("/review")
            library_page = client.get(
                "/review?view=library&mastery=&difficulty=&search=appointment"
            )
            today_page = client.get("/today")

            review_item_id = created.json()["review_item_id"]
            rated = client.post(
                f"/api/reviews/{review_item_id}/rate",
                json={
                    "rating": "good",
                    "request_id": "4d56d68a-fd50-44c8-a014-ef48ece692b4",
                },
            )
            repeated = client.post(
                f"/api/reviews/{review_item_id}/rate",
                json={
                    "rating": "good",
                    "request_id": "4d56d68a-fd50-44c8-a014-ef48ece692b4",
                },
            )
            progress_page = client.get("/progress")

        assert created.status_code == 201
        assert created.json()["next_review_date"] == today.isoformat()
        assert duplicate.status_code == 409
        assert review_page.status_code == 200
        assert "make an appointment" in review_page.text
        assert "Again" in review_page.text
        assert library_page.status_code == 200
        assert "全部词块" in library_page.text
        assert today_page.status_code == 200
        assert "今天有 1 项需要复习" in today_page.text
        assert rated.status_code == 200
        assert rated.json()["created"] is True
        assert rated.json()["review_count"] == 1
        assert repeated.status_code == 200
        assert repeated.json()["created"] is False
        assert repeated.json()["review_count"] == 1
        assert progress_page.status_code == 200
        assert "REVIEWS COMPLETED" in progress_page.text


def test_review_page_rejects_invalid_filter() -> None:
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
        app.include_router(review_router)
        app.dependency_overrides[get_review_services] = lambda: services

        with TestClient(app) as client:
            response = client.get("/review?mastery=unknown")

        assert response.status_code == 422


def _add_resources(session: Session) -> None:
    session.add_all(
        [
            LearningResource(
                slug=f"{skill.value}-review-route-resource",
                title=f"{skill.value.title()} review route resource",
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
