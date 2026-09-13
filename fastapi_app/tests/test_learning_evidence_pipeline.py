from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.database import Base
from app.domain.learner_profile.entities import EvidenceStatus
from app.domain.learner_profile.rule_based_evaluator import RuleBasedSkillEvaluator
from app.domain.weakness_detection.entities import SkillClassification
from app.domain.weakness_detection.rule_based_detector import RuleBasedWeaknessDetector
from app.models.learning_evidence import ExerciseAttempt, SkillPerformance, StudySession
from app.models.learner_profile import (
    LearnerProfile,
    LearnerProfileSnapshotModel,
    LearnerSkillSnapshot,
)
from app.models.weakness_detection import (
    WeaknessAssessmentRunModel,
    WeaknessSkillAssessmentModel,
)
from app.repositories.sqlalchemy_ielts import SqlAlchemyIeltsPracticeRepository
from app.repositories.sqlalchemy_learning_evidence import SqlAlchemyLearningEvidenceRepository
from app.repositories.sqlalchemy_learner_profile import SqlAlchemyLearnerProfileRepository
from app.repositories.sqlalchemy_weakness_detection import (
    SqlAlchemyWeaknessAssessmentRepository,
)
from app.seed import import_seed_data
from app.services.ielts_learning_evidence import IeltsLearningEvidenceRecorder
from app.services.ielts_practice import IeltsPracticeService
from app.services.learning_evidence import LearningEvidenceService
from app.services.learner_profile import LearnerProfileService
from app.services.weakness_detection import WeaknessDetectionService


SEED_PATH = Path(__file__).parents[1] / "seed" / "g20_test1.json"


def test_submitted_ielts_attempt_becomes_immutable_learning_evidence() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        import_seed_data(session, SEED_PATH)
        service, profile_service, weakness_service = _services(session)
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
        assert _count(session, LearnerProfile) == 1
        assert _count(session, LearnerProfileSnapshotModel) == 1
        assert _count(session, LearnerSkillSnapshot) == 4
        assert _count(session, WeaknessAssessmentRunModel) == 1
        assert _count(session, WeaknessSkillAssessmentModel) == 4
        first_performance = session.scalar(select(SkillPerformance))
        assert first_performance is not None
        assert first_performance.skill == "listening"
        assert first_performance.accuracy == 1.0
        assert first_performance.correct_item_count == 40
        first_profile = profile_service.get_current_profile("learner")
        assert [item.skill.value for item in first_profile.skills] == [
            "listening",
            "speaking",
            "reading",
            "vocabulary",
        ]
        listening = next(item for item in first_profile.skills if item.skill.value == "listening")
        speaking = next(item for item in first_profile.skills if item.skill.value == "speaking")
        assert listening.score == 100.0
        assert listening.evidence_status is EvidenceStatus.PROVISIONAL
        assert speaking.score is None
        assert speaking.evidence_status is EvidenceStatus.NO_DATA
        first_assessment = weakness_service.get_current_assessment("learner")
        assert first_assessment is not None
        listening_assessment = next(
            item for item in first_assessment.skills if item.skill.value == "listening"
        )
        assert (
            listening_assessment.classification
            is SkillClassification.INSUFFICIENT_EVIDENCE
        )
        assert listening_assessment.scored_snapshot_count == 1
        assert all(
            item.classification is SkillClassification.INSUFFICIENT_EVIDENCE
            for item in first_assessment.skills
        )
        unchanged_profile = profile_service.refresh_profile("learner")
        assert unchanged_profile.created is False
        assert unchanged_profile.id == first_profile.id
        assert _count(session, LearnerProfileSnapshotModel) == 1
        unchanged_assessment = weakness_service.refresh_assessment("learner")
        assert unchanged_assessment.created is False
        assert unchanged_assessment.id == first_assessment.id
        assert _count(session, WeaknessAssessmentRunModel) == 1

        service.submit("g20-test-1-listening", "learner")

        assert _count(session, StudySession) == 1
        assert _count(session, ExerciseAttempt) == 40
        assert _count(session, LearnerProfileSnapshotModel) == 1
        assert _count(session, WeaknessAssessmentRunModel) == 1

        service.save_answer("g20-test-1-listening", "learner", 1, "definitely wrong")
        second_result = service.submit("g20-test-1-listening", "learner")

        assert second_result["score"] == 39
        assert _count(session, StudySession) == 2
        assert _count(session, ExerciseAttempt) == 80
        assert _count(session, SkillPerformance) == 2
        assert _count(session, LearnerProfileSnapshotModel) == 2
        assert _count(session, LearnerSkillSnapshot) == 8
        assert _count(session, WeaknessAssessmentRunModel) == 2
        assert _count(session, WeaknessSkillAssessmentModel) == 8
        sessions = session.scalars(select(StudySession).order_by(StudySession.source_revision)).all()
        assert [item.source_revision for item in sessions] == [1, 2]
        assert [item.accuracy for item in sessions] == [1.0, 39 / 40]
        current_profile = profile_service.get_current_profile("learner")
        listening = next(item for item in current_profile.skills if item.skill.value == "listening")
        assert listening.score == 98.8
        assert listening.evidence_status is EvidenceStatus.ESTABLISHED
        assert listening.sample_count == 2
        current_assessment = weakness_service.get_current_assessment("learner")
        assert current_assessment is not None
        listening_assessment = next(
            item for item in current_assessment.skills if item.skill.value == "listening"
        )
        assert listening_assessment.classification is SkillClassification.STRONG
        assert listening_assessment.smoothed_score == 99.4
        assert listening_assessment.scored_snapshot_count == 2
        assert listening_assessment.evidence_snapshot_ids == (
            first_profile.id,
            current_profile.id,
        )


def _services(
    session: Session,
) -> tuple[IeltsPracticeService, LearnerProfileService, WeaknessDetectionService]:
    evidence_service = LearningEvidenceService(SqlAlchemyLearningEvidenceRepository(session))
    profile_service = LearnerProfileService(
        evidence_service,
        SqlAlchemyLearnerProfileRepository(session),
        RuleBasedSkillEvaluator(),
    )
    weakness_service = WeaknessDetectionService(
        profile_service,
        SqlAlchemyWeaknessAssessmentRepository(session),
        RuleBasedWeaknessDetector(),
    )
    recorder = IeltsLearningEvidenceRecorder(
        evidence_service,
        profile_service,
        weakness_service,
    )
    practice_service = IeltsPracticeService(
        SqlAlchemyIeltsPracticeRepository(session), submission_observer=recorder
    )
    return practice_service, profile_service, weakness_service


def _count(session: Session, model) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0
