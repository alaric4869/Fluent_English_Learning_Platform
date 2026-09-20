from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.routes.practice import (
    get_service as get_practice_service,
    get_services as get_practice_services,
    router as practice_router,
)
from app.api.routes.speaking import get_services, router as speaking_router
from app.composition import build_application_services
from app.config import FASTAPI_ROOT, settings
from app.database import Base
from app.domain.speaking.entities import (
    RetellingDraftStatus,
    RetellingWorkspaceInput,
    SpeakingPracticeStatus,
)
from app.models.learning_evidence import LearningResource, SkillPerformance, StudySession
from app.models.practice_notes import RetellingRecordModel
from app.models.speaking import (
    SpeakingRetellingSubmissionModel,
    SpeakingSentenceProgressModel,
)
from app.seed import import_seed_data


NOW = datetime(2026, 9, 14, 6, 0, tzinfo=timezone.utc)


def test_speaking_service_tracks_sentences_and_revisioned_retelling_evidence() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        import_seed_data(session, settings.seed_path)
        services = build_application_services(session)
        services.speaking.now = lambda: NOW
        resource = _speaking_resource(session)

        workspace = services.speaking.get_workspace("learner", resource.id)
        assert workspace.audio_url == "/media/audio/g20-test-1-listening/1"
        assert len(workspace.sentences) == 10
        assert workspace.record is None

        first_mark = services.speaking.mark_sentence(
            "learner",
            resource.id,
            "restaurant-01",
            SpeakingPracticeStatus.NEED_PRACTICE,
        )
        second_mark = services.speaking.mark_sentence(
            "learner",
            resource.id,
            "restaurant-01",
            SpeakingPracticeStatus.GOOD,
        )
        assert first_mark.practice_count == 1
        assert second_mark.practice_count == 2
        assert _count(session, SpeakingSentenceProgressModel) == 1

        services.speaking.save_workspace_draft(
            "learner",
            resource.id,
            RetellingWorkspaceInput(
                written_outline="birthday → requirements → recommendation",
                intended_vocabulary=("for a special occasion", "great atmosphere"),
                retelling_text="The woman needed a restaurant for her sister's birthday.",
                mistakes="I paused before restaurant.",
                improved_version="She asked her friend to recommend a restaurant.",
                practice_status=SpeakingPracticeStatus.GOOD,
                active_duration_seconds=540,
                perceived_difficulty=4,
                confidence=3,
            ),
        )
        first_record, first_submission, first_session_id = services.speaking.submit(
            "learner", resource.id
        )
        repeated_record, repeated_submission, repeated_session_id = services.speaking.submit(
            "learner", resource.id
        )

        assert first_record.status is RetellingDraftStatus.SUBMITTED
        assert first_submission.revision == 1
        assert repeated_submission.created is False
        assert repeated_record.submission_revision == 1
        assert repeated_session_id == first_session_id
        assert _count(session, SpeakingRetellingSubmissionModel) == 1
        assert _count(session, StudySession) == 1

        edited = services.speaking.save_workspace_draft(
            "learner",
            resource.id,
            RetellingWorkspaceInput(
                written_outline="revised outline",
                intended_vocabulary=("I'd definitely recommend",),
                retelling_text="The woman asked for advice and the man recommended the Junction.",
                improved_version="The man recommended the Junction for a special occasion.",
                practice_status=SpeakingPracticeStatus.GOOD,
                active_duration_seconds=660,
                perceived_difficulty=3,
                confidence=4,
            ),
        )
        assert edited.status is RetellingDraftStatus.IN_PROGRESS
        _, second_submission, _ = services.speaking.submit("learner", resource.id)

        assert second_submission.revision == 2
        assert _count(session, RetellingRecordModel) == 1
        assert _count(session, SpeakingRetellingSubmissionModel) == 2
        assert _count(session, StudySession) == 2
        performance = session.scalars(
            select(SkillPerformance).order_by(SkillPerformance.id.desc())
        ).first()
        assert performance.skill == "speaking"
        assert performance.accuracy is None
        assert performance.metrics["marked_sentence_count"] == 1
        assert performance.metrics["awaiting_ai_evaluation"] is True


def test_speaking_workspace_is_web_native_and_uses_real_audio() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        import_seed_data(session, settings.seed_path)
        services = build_application_services(session)
        resource = _speaking_resource(session)
        app = FastAPI()
        app.mount(
            "/static",
            StaticFiles(directory=FASTAPI_ROOT / "app" / "static"),
            name="static",
        )
        app.include_router(practice_router)
        app.include_router(speaking_router)
        app.dependency_overrides[get_services] = lambda: services
        app.dependency_overrides[get_practice_services] = lambda: services
        app.dependency_overrides[get_practice_service] = lambda: services.ielts_practice

        with TestClient(app) as client:
            index = client.get("/ielts")
            page = client.get(f"/speaking/{resource.id}")
            audio = client.get("/media/audio/g20-test-1-listening/1")
            marked = client.put(
                f"/api/speaking/{resource.id}/sentences/restaurant-02",
                json={"practice_status": "mastered"},
            )
            saved = client.put(
                f"/api/speaking/{resource.id}/draft",
                json={
                    "written_outline": "birthday, restaurant, reasons",
                    "intended_vocabulary": ["for a special occasion"],
                    "retelling_text": "The woman asked for restaurant advice.",
                    "mistakes": "",
                    "improved_version": "",
                    "practice_status": "good",
                    "active_duration_seconds": 75,
                    "perceived_difficulty": 3,
                    "confidence": 3,
                },
            )
            submitted = client.post(f"/api/speaking/{resource.id}/submit")
            evaluation = client.post(f"/api/speaking/{resource.id}/evaluation")

        assert index.status_code == 200
        assert "17 modules available" in index.text
        assert "TESTS 1–4" in index.text
        assert "跟读与复述 Speaking" in index.text
        assert page.status_code == 200
        assert "been meaning to ask you" in page.text
        assert "隐藏 Transcript" in page.text
        assert "VOICE RECORDING · LATER" in page.text
        assert "iframe" not in page.text
        assert audio.status_code == 200
        assert audio.headers["content-type"].startswith("audio/mpeg")
        assert marked.status_code == 200
        assert marked.json()["practice_status"] == "mastered"
        assert saved.status_code == 200
        assert saved.json()["retelling_text"].startswith("The woman")
        assert submitted.status_code == 200
        assert submitted.json()["submission_revision"] == 1
        assert evaluation.status_code == 503
        assert "AI evaluation is not configured" in evaluation.json()["detail"]


def _speaking_resource(session: Session) -> LearningResource:
    return session.scalar(
        select(LearningResource).where(
            LearningResource.slug == "g20-test-1-speaking-restaurants"
        )
    )


def _count(session: Session, model) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0
