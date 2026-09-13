from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.routes.notebook import get_services, router as notebook_router
from app.api.routes.review import get_services as get_review_services
from app.api.routes.review import router as review_router
from app.composition import build_application_services
from app.config import FASTAPI_ROOT
from app.database import Base


def test_notebook_forms_and_sentence_review_share_persisted_state() -> None:
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
        app.include_router(notebook_router)
        app.include_router(review_router)
        app.dependency_overrides[get_services] = lambda: services
        app.dependency_overrides[get_review_services] = lambda: services
        today = datetime.now(ZoneInfo("Australia/Sydney")).date()

        with TestClient(app) as client:
            note = client.post(
                "/api/notebook/notes",
                json={
                    "note_type": "grammar",
                    "title": "Past tense",
                    "content": "Remember the -ed ending.",
                    "tags": ["grammar", "speaking"],
                },
            )
            sentence = client.post(
                "/api/listening/sentences",
                json={
                    "sentence": "Would it be possible to move it to Friday?",
                    "meaning": "可以改到周五吗？",
                    "learned_on": (today - timedelta(days=1)).isoformat(),
                    "practice_status": "could_not_hear",
                    "note": "Weak form of would it be",
                    "source_context": "Appointment audio",
                    "add_to_review": True,
                },
            )
            retelling = client.post(
                "/api/speaking/retellings",
                json={
                    "prompt": "Retell the appointment call.",
                    "written_outline": "call, explain, confirm",
                    "intended_vocabulary": ["reschedule my appointment"],
                    "mistakes": "Slow response",
                    "improved_version": "She called to reschedule her appointment.",
                    "practice_status": "need_practice",
                },
            )
            listening_page = client.get("/notebook?view=listening")
            review_page = client.get("/review")
            updated = client.patch(
                f"/api/listening/sentences/{sentence.json()['id']}/status",
                json={"practice_status": "understood"},
            )

        assert note.status_code == 201
        assert sentence.status_code == 201
        assert sentence.json()["review_item_id"] is not None
        assert retelling.status_code == 201
        assert retelling.json()["voice_recording_reference"] is None
        assert listening_page.status_code == 200
        assert "Would it be possible to move it to Friday?" in listening_page.text
        assert review_page.status_code == 200
        assert "听力难句" in review_page.text
        assert updated.status_code == 200
        assert updated.json()["practice_status"] == "understood"
