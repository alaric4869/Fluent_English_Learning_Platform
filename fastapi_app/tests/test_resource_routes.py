from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.routes.resources import get_services, router
from app.composition import build_application_services
from app.config import FASTAPI_ROOT
from app.database import Base


def test_resource_library_create_edit_favorite_and_archive_flow() -> None:
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
        payload = {
            "title": "Real Australian Conversation",
            "resource_type": "video",
            "skill": "listening",
            "topic": "Australian daily life",
            "difficulty": "intermediate",
            "estimated_duration_minutes": 18,
            "source_url": "https://example.com/video",
            "description": "A natural reception conversation.",
            "content_text": "",
            "transcript": "Would it be possible to move the appointment?",
            "notes": "Notice the weak forms.",
            "tags": ["Australia", "appointments"],
            "priority": 70,
        }

        with TestClient(app) as client:
            created = client.post("/api/resources", json=payload)
            resource_id = created.json()["id"]
            library = client.get("/library?search=reception&skill=listening")
            detail = client.get(f"/library/{resource_id}")
            favorite = client.patch(
                f"/api/resources/{resource_id}/state", json={"favorite": True}
            )
            favorites = client.get("/library?view=favorites")
            changed_payload = {**payload, "title": "Updated Australian Conversation"}
            updated = client.put(
                f"/api/resources/{resource_id}", json=changed_payload
            )
            archived = client.patch(
                f"/api/resources/{resource_id}/state", json={"archived": True}
            )
            active_page = client.get("/library")
            archived_page = client.get("/library?view=archived")

        assert created.status_code == 201
        assert library.status_code == 200
        assert "Real Australian Conversation" in library.text
        assert detail.status_code == 200
        assert "Would it be possible to move the appointment?" in detail.text
        assert favorite.status_code == 200
        assert favorite.json()["favorite"] is True
        assert "Real Australian Conversation" in favorites.text
        assert updated.status_code == 200
        assert updated.json()["title"] == "Updated Australian Conversation"
        assert archived.status_code == 200
        assert archived.json()["archived"] is True
        assert "Updated Australian Conversation" not in active_page.text
        assert "Updated Australian Conversation" in archived_page.text


def test_resource_routes_reject_unsafe_url_and_empty_state_change() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        services = build_application_services(session)
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_services] = lambda: services
        payload = {
            "title": "Unsafe",
            "resource_type": "video",
            "skill": "listening",
            "topic": "Daily life",
            "estimated_duration_minutes": 20,
            "source_url": "file:///private/audio.mp3",
        }

        with TestClient(app) as client:
            unsafe = client.post("/api/resources", json=payload)
            missing_state = client.patch("/api/resources/999/state", json={})

        assert unsafe.status_code == 422
        assert missing_state.status_code == 422
