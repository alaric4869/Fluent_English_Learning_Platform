from app.domain.ielts.entities import GradeResult
from app.domain.learning_evidence.entities import (
    CompletedStudySession,
    ExerciseAttemptEvidence,
    LearningEvidenceBundle,
    Skill,
    SkillPerformanceEvidence,
)
from app.services.learning_evidence import LearningEvidenceService


class IeltsLearningEvidenceRecorder:
    """Translate an IELTS submission into the generic learning evidence model."""

    def __init__(self, service: LearningEvidenceService) -> None:
        self.service = service

    def record_submission(
        self,
        practice_set: dict,
        attempt: dict,
        grade: GradeResult,
    ) -> None:
        self.service.record(build_ielts_evidence_bundle(practice_set, attempt, grade))


def build_ielts_evidence_bundle(
    practice_set: dict,
    attempt: dict,
    grade: GradeResult,
) -> LearningEvidenceBundle:
    resource_id = practice_set.get("learning_resource_id")
    if resource_id is None:
        raise ValueError("IELTS practice set is not linked to a learning resource")
    if not attempt.get("submitted_at"):
        raise ValueError("IELTS attempt must be submitted before evidence is recorded")

    questions = {
        question["number"]: question
        for section in practice_set["sections"]
        for question in section["questions"]
    }
    skill = Skill(practice_set["skill"])
    revision = int(attempt["submission_revision"])
    completed_at = attempt["submitted_at"]
    accuracy = grade.score / grade.total if grade.total else 0.0
    exercises = tuple(
        ExerciseAttemptEvidence(
            exercise_id=f"{practice_set['slug']}:question:{result.number}",
            submitted_answer=result.submitted_answer,
            correct=result.is_correct,
            score=1.0 if result.is_correct else 0.0,
            max_score=1.0,
            attempt_number=revision,
            prompt_snapshot=questions[result.number]["prompt"],
            correct_answers=result.correct_answers,
            explanation_snapshot=result.explanation,
        )
        for result in grade.questions
    )
    incorrect_count = grade.total - grade.score
    session = CompletedStudySession(
        user_key=attempt["user_key"],
        resource_id=resource_id,
        skill=skill,
        source_type="ielts_practice_attempt",
        source_id=str(attempt["id"]),
        source_revision=revision,
        started_at=attempt["started_at"],
        completed_at=completed_at,
        accuracy=accuracy,
        attempt_count=revision,
        incorrect_item_count=incorrect_count,
    )
    performance = SkillPerformanceEvidence(
        user_key=attempt["user_key"],
        skill=skill,
        accuracy=accuracy,
        item_count=grade.total,
        correct_item_count=grade.score,
        incorrect_item_count=incorrect_count,
        occurred_at=completed_at,
        metrics={
            "raw_score": grade.score,
            "maximum_score": grade.total,
            "source": "ielts",
            "submission_revision": revision,
        },
    )
    return LearningEvidenceBundle(session=session, exercises=exercises, performance=performance)
