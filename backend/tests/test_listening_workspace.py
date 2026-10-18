from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.routes.listening import get_services, router
from app.composition import build_application_services
from app.config import FASTAPI_ROOT
from app.database import Base
from app.models.learning_evidence import LearningResource
from app.models.practice_notes import SavedSentenceModel
from app.models.vocabulary import ReviewItemModel


def test_listening_workspace_embeds_youtube_and_marks_transcript_idempotently() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        resource = LearningResource(
            slug="personal-natural-listening",
            title="Natural café conversation",
            resource_type="video",
            skill="listening",
            topic="Ordering coffee",
            difficulty="intermediate",
            estimated_duration_minutes=12,
            source_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            content={},
            tags=["conversation"],
            priority=70,
            active=True,
            owner_user_key="local-user",
            transcript="Could I get a flat white, please? Sure. Would you like sugar?",
        )
        session.add(resource)
        session.commit()
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
            page = client.get(f"/listening/{resource.id}")

            assert page.status_code == 200
            assert "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ" in page.text
            assert "Could I get a flat white, please?" in page.text
            assert "Would you like sugar?" in page.text

            difficult = client.post(
                f"/api/listening/resources/{resource.id}/sentences",
                json={
                    "sentence": "Could I get a flat white, please?",
                    "practice_status": "difficult",
                },
            )
            assert difficult.status_code == 200
            assert difficult.json()["review_item_id"] is not None

            understood = client.post(
                f"/api/listening/resources/{resource.id}/sentences",
                json={
                    "sentence": "Could I get a flat white, please?",
                    "practice_status": "understood",
                },
            )
            assert understood.status_code == 200
            assert understood.json()["id"] == difficult.json()["id"]
            assert understood.json()["practice_status"] == "understood"

            invented = client.post(
                f"/api/listening/resources/{resource.id}/sentences",
                json={
                    "sentence": "This sentence is not in the transcript.",
                    "practice_status": "difficult",
                },
            )
            assert invented.status_code == 422

        assert session.scalar(select(func.count()).select_from(SavedSentenceModel)) == 1
        assert session.scalar(select(func.count()).select_from(ReviewItemModel)) == 1
