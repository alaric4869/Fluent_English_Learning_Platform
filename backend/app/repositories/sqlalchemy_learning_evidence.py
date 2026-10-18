from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.learning_evidence.entities import (
    HistoricalSkillPerformance,
    LearningEvidenceBundle,
    RecordedLearningEvidence,
    Skill,
)
from app.models.learning_evidence import ExerciseAttempt, SkillPerformance, StudySession


class SqlAlchemyLearningEvidenceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def record(self, bundle: LearningEvidenceBundle) -> RecordedLearningEvidence:
        session_data = bundle.session
        existing = self.session.scalar(
            select(StudySession).where(
                StudySession.user_key == session_data.user_key,
                StudySession.source_type == session_data.source_type,
                StudySession.source_id == session_data.source_id,
                StudySession.source_revision == session_data.source_revision,
            )
        )
        if existing is not None:
            return RecordedLearningEvidence(study_session_id=existing.id, created=False)

        study_session = StudySession(
            user_key=session_data.user_key,
            resource_id=session_data.resource_id,
            skill=session_data.skill.value,
            source_type=session_data.source_type,
            source_id=session_data.source_id,
            source_revision=session_data.source_revision,
            status="completed",
            started_at=session_data.started_at,
            completed_at=session_data.completed_at,
            actual_duration_seconds=session_data.actual_duration_seconds,
            perceived_difficulty=session_data.perceived_difficulty,
            confidence=session_data.confidence,
            accuracy=session_data.accuracy,
            attempt_count=session_data.attempt_count,
            hard_item_count=session_data.hard_item_count,
            incorrect_item_count=session_data.incorrect_item_count,
            notes=session_data.notes,
        )
        self.session.add(study_session)
        self.session.flush()
        self.session.add_all(
            [
                ExerciseAttempt(
                    study_session_id=study_session.id,
                    exercise_id=item.exercise_id,
                    submitted_answer=item.submitted_answer,
                    correct=item.correct,
                    score=item.score,
                    max_score=item.max_score,
                    attempt_number=item.attempt_number,
                    confidence=item.confidence,
                    response_time_ms=item.response_time_ms,
                    prompt_snapshot=item.prompt_snapshot,
                    correct_answers=list(item.correct_answers),
                    explanation_snapshot=item.explanation_snapshot,
                )
                for item in bundle.exercises
            ]
        )
        performance = bundle.performance
        self.session.add(
            SkillPerformance(
                study_session_id=study_session.id,
                user_key=performance.user_key,
                skill=performance.skill.value,
                accuracy=performance.accuracy,
                item_count=performance.item_count,
                correct_item_count=performance.correct_item_count,
                incorrect_item_count=performance.incorrect_item_count,
                hard_item_count=performance.hard_item_count,
                confidence=performance.confidence,
                perceived_difficulty=performance.perceived_difficulty,
                occurred_at=performance.occurred_at,
                metrics=performance.metrics or {},
            )
        )
        self.session.commit()
        return RecordedLearningEvidence(study_session_id=study_session.id, created=True)

    def list_recent_skill_performance(
        self,
        user_key: str,
        skill: Skill,
        limit: int,
    ) -> tuple[HistoricalSkillPerformance, ...]:
        statement = (
            select(SkillPerformance)
            .where(
                SkillPerformance.user_key == user_key,
                SkillPerformance.skill == skill.value,
            )
            .order_by(SkillPerformance.occurred_at.desc(), SkillPerformance.id.desc())
            .limit(limit)
        )
        return tuple(self._to_historical(item) for item in self.session.scalars(statement))

    @staticmethod
    def _to_historical(item: SkillPerformance) -> HistoricalSkillPerformance:
        return HistoricalSkillPerformance(
            id=item.id,
            study_session_id=item.study_session_id,
            user_key=item.user_key,
            skill=Skill(item.skill),
            accuracy=item.accuracy,
            item_count=item.item_count,
            correct_item_count=item.correct_item_count,
            incorrect_item_count=item.incorrect_item_count,
            hard_item_count=item.hard_item_count,
            confidence=item.confidence,
            perceived_difficulty=item.perceived_difficulty,
            occurred_at=item.occurred_at,
            metrics=dict(item.metrics),
        )
