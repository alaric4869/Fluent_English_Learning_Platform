from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.frontend_dependencies import get_frontend_services
from app.api.routes.frontend_insights import router as insights_router
from app.api.routes.frontend_notebook import router as notebook_router
from app.api.routes.frontend_resources import router as resources_router
from app.api.routes.frontend_review import router as review_router
from app.composition import build_application_services
from app.database import Base
from app.domain.learning_evidence.entities import Skill
from app.models.learning_evidence import LearningResource


def test_react_core_learning_contracts_support_reads_and_writes() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        session.add_all(
            [
                LearningResource(
                    slug=f"{skill.value}-m21-contract",
                    title=f"{skill.value.title()} M21 resource",
                    resource_type="practice",
                    skill=skill.value,
                    topic="IELTS General Training",
                    difficulty="intermediate",
                    estimated_duration_minutes=25,
                    description="M21 API contract resource",
                    content={},
                    tags=["m21"],
                    priority=50,
                    active=True,
                )
                for skill in Skill
            ]
        )
        session.commit()
        services = build_application_services(session)
        app = FastAPI()
        app.include_router(resources_router)
        app.include_router(review_router)
        app.include_router(notebook_router)
        app.include_router(insights_router)
        app.dependency_overrides[get_frontend_services] = lambda: services

        with TestClient(app) as client:
            library = client.get("/api/v1/library")
            created_resource = client.post(
                "/api/v1/library",
                json={
                    "title": "Personal podcast",
                    "resource_type": "podcast",
                    "skill": "listening",
                    "topic": "Australian English",
                    "difficulty": "intermediate",
                    "estimated_duration_minutes": 20,
                    "source_url": "https://example.com/podcast",
                    "description": "A personal listening source",
                    "content_text": "",
                    "transcript": "",
                    "notes": "",
                    "tags": ["australia"],
                    "priority": 60,
                },
            )
            resource_id = created_resource.json()["id"]
            favorite = client.patch(
                f"/api/v1/library/{resource_id}/state",
                json={"favorite": True},
            )
            vocabulary = client.post(
                "/api/v1/vocabulary",
                json={
                    "chunk": "make an appointment",
                    "meaning": "arrange a time to meet",
                    "example_sentence": "I need to make an appointment.",
                    "personal_note": "Useful for healthcare",
                    "difficulty": "medium",
                    "source_resource_id": None,
                    "source_context": "Daily life",
                    "tags": ["appointment"],
                },
            )
            review = client.get("/api/v1/review")
            rating = client.post(
                f"/api/v1/reviews/{vocabulary.json()['review_item_id']}/rate",
                json={"rating": "good", "request_id": str(uuid4())},
            )
            note = client.post(
                "/api/v1/notebook/notes",
                json={
                    "note_type": "useful_expression",
                    "title": "Polite request",
                    "content": "Would it be possible to…?",
                    "source_resource_id": None,
                    "source_context": "Appointments",
                    "tags": ["polite"],
                },
            )
            notebook = client.get("/api/v1/notebook")
            history = client.get("/api/v1/history")
            progress = client.get("/api/v1/progress")
            weekly = client.get("/api/v1/weekly-review")

    assert library.status_code == 200
    assert library.json()["total_count"] == len(Skill)
    assert created_resource.status_code == 201
    assert favorite.status_code == 200
    assert favorite.json()["favorite"] is True
    assert vocabulary.status_code == 201
    assert review.status_code == 200
    assert review.json()["due_count"] == 0
    assert review.json()["total_count"] == 1
    assert rating.status_code == 200
    assert rating.json()["mastery_status"] == "learning"
    assert note.status_code == 201
    assert notebook.status_code == 200
    assert notebook.json()["counts"]["notes"] == 1
    assert history.status_code == 200
    assert progress.status_code == 200
    assert len(progress.json()["skills"]) == len(Skill)
    assert weekly.status_code == 200
    assert weekly.json()["recommendations"]
