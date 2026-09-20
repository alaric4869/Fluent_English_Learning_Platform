from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.routes.practice import (
    get_services as get_practice_services,
    router as practice_router,
)
from app.api.routes.writing import get_services, router
from app.composition import build_application_services
from app.config import FASTAPI_ROOT, settings
from app.database import Base
from app.domain.writing.entities import WritingDraftInput, WritingDraftStatus
from app.models.learning_evidence import LearningResource, SkillPerformance, StudySession
from app.models.writing import WritingDraftModel, WritingSubmissionModel
from app.seed import import_seed_data
from app.services.writing import IncompleteWritingDraftError, WritingPracticeService


NOW = datetime(2026, 9, 14, 5, 0, tzinfo=timezone.utc)


def test_writing_service_saves_drafts_and_preserves_submission_revisions() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        import_seed_data(session, settings.seed_path)
        services = build_application_services(session)
        service = _with_fixed_time(services.writing)
        resource = session.scalar(
            select(LearningResource).where(
                LearningResource.slug == "g20-test-1-writing-task-1"
            )
        )

        workspace = service.get_workspace("learner", resource.id)
        assert workspace.minimum_words == 150
        assert workspace.draft is None

        short = service.save_draft(
            "learner",
            resource.id,
            WritingDraftInput("Only a few words.", "Plan", 62, 4, 2),
        )
        assert short.word_count == 4
        with pytest.raises(IncompleteWritingDraftError):
            service.submit("learner", resource.id)

        first_text = " ".join(f"word{index}" for index in range(150))
        service.save_draft(
            "learner",
            resource.id,
            WritingDraftInput(first_text, "Opening; details; request", 1_200, 3, 3),
        )
        first_draft, first_submission, first_session_id = service.submit(
            "learner", resource.id
        )
        repeated_draft, repeated_submission, repeated_session_id = service.submit(
            "learner", resource.id
        )

        assert first_draft.status is WritingDraftStatus.SUBMITTED
        assert first_submission.revision == 1
        assert repeated_submission.created is False
        assert repeated_draft.submission_revision == 1
        assert repeated_session_id == first_session_id
        assert _count(session, WritingSubmissionModel) == 1
        assert _count(session, StudySession) == 1

        second_text = first_text + " improved"
        edited = service.save_draft(
            "learner",
            resource.id,
            WritingDraftInput(second_text, "Revised plan", 1_350, 3, 4),
        )
        assert edited.status is WritingDraftStatus.IN_PROGRESS
        _, second_submission, _ = service.submit("learner", resource.id)

        assert second_submission.revision == 2
        assert _count(session, WritingDraftModel) == 1
        assert _count(session, WritingSubmissionModel) == 2
        assert _count(session, StudySession) == 2
        performance = session.scalars(
            select(SkillPerformance).order_by(SkillPerformance.id.desc())
        ).first()
        assert performance.skill == "writing"
        assert performance.accuracy is None
        assert performance.metrics["word_count"] == 151
        assert performance.metrics["awaiting_ai_evaluation"] is True


def test_writing_workspace_is_web_native_and_submit_validates_word_count() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        import_seed_data(session, settings.seed_path)
        services = build_application_services(session)
        resource = session.scalar(
            select(LearningResource).where(
                LearningResource.slug == "g20-test-1-writing-task-1"
            )
        )
        app = FastAPI()
        app.mount(
            "/static",
            StaticFiles(directory=FASTAPI_ROOT / "app" / "static"),
            name="static",
        )
        app.include_router(practice_router)
        app.include_router(router)
        app.dependency_overrides[get_services] = lambda: services
        app.dependency_overrides[get_practice_services] = lambda: services

        with TestClient(app) as client:
            index = client.get("/ielts")
            page = client.get(f"/writing/{resource.id}")
            saved = client.put(
                f"/api/writing/{resource.id}/draft",
                json={
                    "response_text": "Too short",
                    "outline": "Three points",
                    "active_duration_seconds": 15,
                    "perceived_difficulty": 4,
                    "confidence": 2,
                },
            )
            submitted = client.post(f"/api/writing/{resource.id}/submit")

        assert index.status_code == 200
        assert "17 modules available" in index.text
        assert "TESTS 1–4" in index.text
        assert index.text.index("Writing Task 1") < index.text.index("Writing Task 2")
        assert page.status_code == 200
        assert "Write your answer here" in page.text
        assert "iframe" not in page.text
        assert "PDF" not in page.text
        assert saved.status_code == 200
        assert saved.json()["word_count"] == 2
        assert submitted.status_code == 422
        assert submitted.json()["detail"]["minimum_words"] == 150


def _with_fixed_time(service: WritingPracticeService) -> WritingPracticeService:
    service.now = lambda: NOW
    return service


def _count(session: Session, model) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0
