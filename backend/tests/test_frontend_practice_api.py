from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.frontend_dependencies import get_frontend_services
from app.api.routes.frontend_practice import router
from app.composition import build_application_services
from app.config import settings
from app.database import Base
from app.models.learning_evidence import LearningResource
from app.seed import import_seed_data


def test_react_writing_speaking_and_listening_workspace_contracts() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        import_seed_data(session, settings.seed_path)
        personal_listening = LearningResource(
            slug="react-listening-contract",
            title="React listening contract",
            resource_type="podcast",
            skill="listening",
            topic="Daily life",
            difficulty="intermediate",
            estimated_duration_minutes=20,
            source_url="https://example.com/audio.mp3",
            transcript="Could I make an appointment? Yes, tomorrow is available.",
            content={},
            tags=["contract"],
            priority=50,
            active=True,
        )
        session.add(personal_listening)
        session.commit()
        services = build_application_services(session)
        writing_id = _resource_id(session, "g20-test-1-writing-task-1")
        speaking_id = _resource_id(session, "g20-test-1-speaking-restaurants")
        listening_id = personal_listening.id
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_frontend_services] = lambda: services

        with TestClient(app) as client:
            writing = client.get(f"/api/v1/writing/{writing_id}")
            writing_draft = client.put(
                f"/api/v1/writing/{writing_id}/draft",
                json={
                    "response_text": "Short draft",
                    "outline": "Plan",
                    "active_duration_seconds": 10,
                    "perceived_difficulty": 3,
                    "confidence": 2,
                },
            )
            writing_submit = client.post(f"/api/v1/writing/{writing_id}/submit")
            speaking = client.get(f"/api/v1/speaking/{speaking_id}")
            sentence_key = speaking.json()["sentences"][0]["key"]
            speaking_mark = client.put(
                f"/api/v1/speaking/{speaking_id}/sentences/{sentence_key}",
                json={"practice_status": "good"},
            )
            speaking_draft = client.put(
                f"/api/v1/speaking/{speaking_id}/draft",
                json={"written_outline": "A short outline", "retelling_text": "A short retelling"},
            )
            speaking_submit = client.post(f"/api/v1/speaking/{speaking_id}/submit")
            listening = client.get(f"/api/v1/listening/{listening_id}")
            sentence = listening.json()["sentences"][0]["text"]
            listening_mark = client.post(
                f"/api/v1/listening/{listening_id}/sentences",
                json={"sentence": sentence, "practice_status": "difficult"},
            )

    assert writing.status_code == 200
    assert writing.json()["minimum_words"] == 150
    assert writing_draft.status_code == 200
    assert writing_draft.json()["word_count"] == 2
    assert writing_submit.status_code == 422
    assert speaking.status_code == 200
    assert speaking.json()["audio_url"].startswith("/media/audio/")
    assert speaking_mark.status_code == 200
    assert speaking_draft.status_code == 200
    assert speaking_submit.status_code == 200
    assert listening.status_code == 200
    assert listening.json()["media_kind"] in {"youtube", "audio", "local_parts", "external"}
    assert listening.json()["sentences"]
    assert listening_mark.status_code == 200
    assert listening_mark.json()["review_item_id"] is not None


def _resource_id(session: Session, slug: str) -> int:
    resource_id = session.scalar(select(LearningResource.id).where(LearningResource.slug == slug))
    assert resource_id is not None
    return resource_id
