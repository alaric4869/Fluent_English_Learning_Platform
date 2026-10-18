from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.composition import build_application_services
from app.config import settings
from app.database import Base
from app.domain.ai_evaluation.mock_evaluator import MockWorkEvaluator
from app.domain.speaking.entities import RetellingWorkspaceInput
from app.domain.writing.entities import WritingDraftInput
from app.models.ai_evaluation import WorkEvaluationModel
from app.models.learning_evidence import LearningResource
from app.repositories.sqlalchemy_ai_evaluation import SqlAlchemyWorkEvaluationRepository
from app.repositories.sqlalchemy_resources import SqlAlchemyResourceRepository
from app.repositories.sqlalchemy_speaking import SqlAlchemySpeakingPracticeRepository
from app.repositories.sqlalchemy_writing import SqlAlchemyWritingRepository
from app.seed import import_seed_data
from app.services.ai_evaluation import LearningWorkEvaluationService


def test_writing_evaluation_is_idempotent_and_separate_from_authored_work() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        import_seed_data(session, settings.seed_path)
        services = build_application_services(session)
        resource = _resource(session, "g20-test-1-writing-task-1")
        original = " ".join(f"word{index}" for index in range(150))
        services.writing.save_draft(
            "learner",
            resource.id,
            WritingDraftInput(original, "A clear outline", 900, 3, 3),
        )
        _, submission, _ = services.writing.submit("learner", resource.id)
        evaluator = _evaluation_service(session)

        first = evaluator.evaluate_writing("learner", resource.id)
        repeated = evaluator.evaluate_writing("learner", resource.id)
        saved_submission = SqlAlchemyWritingRepository(session).get_submission(
            "learner",
            resource.id,
            submission.revision,
        )

        assert first.created is True
        assert repeated.created is False
        assert first.id == repeated.id
        assert first.result.overall_score == 60
        assert saved_submission.response_snapshot == original
        assert session.scalar(
            select(func.count()).select_from(WorkEvaluationModel)
        ) == 1


def test_retelling_evaluation_uses_submission_snapshot() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        import_seed_data(session, settings.seed_path)
        services = build_application_services(session)
        resource = _resource(session, "g20-test-1-speaking-restaurants")
        retelling = "The caller wanted a restaurant for a birthday celebration."
        services.speaking.save_workspace_draft(
            "learner",
            resource.id,
            RetellingWorkspaceInput(
                written_outline="occasion → recommendation",
                intended_vocabulary=("for a special occasion",),
                retelling_text=retelling,
                active_duration_seconds=240,
            ),
        )
        services.speaking.submit("learner", resource.id)

        evaluation = _evaluation_service(session).evaluate_retelling(
            "learner",
            resource.id,
        )

        assert evaluation.request.learner_text == retelling
        assert evaluation.request.skill.value == "speaking"
        assert evaluation.result.provider_name == "mock"


def _evaluation_service(session: Session) -> LearningWorkEvaluationService:
    return LearningWorkEvaluationService(
        SqlAlchemyWorkEvaluationRepository(session),
        MockWorkEvaluator(),
        SqlAlchemyResourceRepository(session),
        SqlAlchemyWritingRepository(session),
        SqlAlchemySpeakingPracticeRepository(session),
    )


def _resource(session: Session, slug: str) -> LearningResource:
    return session.scalar(select(LearningResource).where(LearningResource.slug == slug))
