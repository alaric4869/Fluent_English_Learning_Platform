from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.database import Base
from app.models.learning_evidence import ExerciseAttempt, SkillPerformance, StudySession
from app.repositories.sqlalchemy_ielts import SqlAlchemyIeltsPracticeRepository
from app.repositories.sqlalchemy_learning_evidence import SqlAlchemyLearningEvidenceRepository
from app.seed import import_seed_data
from app.services.ielts_learning_evidence import IeltsLearningEvidenceRecorder
from app.services.ielts_practice import IeltsPracticeService
from app.services.learning_evidence import LearningEvidenceService


SEED_PATH = Path(__file__).parents[1] / "seed" / "g20_test1.json"


def test_submitted_ielts_attempt_becomes_immutable_learning_evidence() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        import_seed_data(session, SEED_PATH)
        service = _practice_service(session)
        workspace = service.get_practice_workspace("g20-test-1-listening", "learner")
        questions = [
            question
            for section in workspace["practice_set"]["sections"]
            for question in section["questions"]
        ]
        for question in questions:
            service.save_answer(
                "g20-test-1-listening",
                "learner",
                question["number"],
                question["accepted_answers"][0],
            )

        first_result = service.submit("g20-test-1-listening", "learner")

        assert first_result["score"] == 40
        assert _count(session, StudySession) == 1
        assert _count(session, ExerciseAttempt) == 40
        assert _count(session, SkillPerformance) == 1
        first_performance = session.scalar(select(SkillPerformance))
        assert first_performance is not None
        assert first_performance.skill == "listening"
        assert first_performance.accuracy == 1.0
        assert first_performance.correct_item_count == 40

        service.submit("g20-test-1-listening", "learner")

        assert _count(session, StudySession) == 1
        assert _count(session, ExerciseAttempt) == 40

        service.save_answer("g20-test-1-listening", "learner", 1, "definitely wrong")
        second_result = service.submit("g20-test-1-listening", "learner")

        assert second_result["score"] == 39
        assert _count(session, StudySession) == 2
        assert _count(session, ExerciseAttempt) == 80
        assert _count(session, SkillPerformance) == 2
        sessions = session.scalars(select(StudySession).order_by(StudySession.source_revision)).all()
        assert [item.source_revision for item in sessions] == [1, 2]
        assert [item.accuracy for item in sessions] == [1.0, 39 / 40]


def _practice_service(session: Session) -> IeltsPracticeService:
    evidence_service = LearningEvidenceService(SqlAlchemyLearningEvidenceRepository(session))
    recorder = IeltsLearningEvidenceRecorder(evidence_service)
    return IeltsPracticeService(
        SqlAlchemyIeltsPracticeRepository(session),
        submission_observer=recorder,
    )


def _count(session: Session, model) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0
