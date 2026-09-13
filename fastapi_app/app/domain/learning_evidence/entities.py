from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Skill(StrEnum):
    LISTENING = "listening"
    SPEAKING = "speaking"
    READING = "reading"
    VOCABULARY = "vocabulary"


@dataclass(frozen=True)
class HistoricalSkillPerformance:
    id: int
    study_session_id: int
    user_key: str
    skill: Skill
    accuracy: float
    item_count: int
    correct_item_count: int
    incorrect_item_count: int
    hard_item_count: int | None
    confidence: int | None
    perceived_difficulty: int | None
    occurred_at: datetime
    metrics: dict


@dataclass(frozen=True)
class CompletedStudySession:
    user_key: str
    resource_id: int
    skill: Skill
    source_type: str
    source_id: str
    source_revision: int
    started_at: datetime
    completed_at: datetime
    accuracy: float
    attempt_count: int
    incorrect_item_count: int
    actual_duration_seconds: int | None = None
    perceived_difficulty: int | None = None
    confidence: int | None = None
    hard_item_count: int | None = None
    notes: str = ""


@dataclass(frozen=True)
class ExerciseAttemptEvidence:
    exercise_id: str
    submitted_answer: str
    correct: bool
    score: float
    max_score: float
    attempt_number: int
    prompt_snapshot: str
    correct_answers: tuple[str, ...]
    explanation_snapshot: str
    confidence: int | None = None
    response_time_ms: int | None = None


@dataclass(frozen=True)
class SkillPerformanceEvidence:
    user_key: str
    skill: Skill
    accuracy: float
    item_count: int
    correct_item_count: int
    incorrect_item_count: int
    occurred_at: datetime
    hard_item_count: int | None = None
    confidence: int | None = None
    perceived_difficulty: int | None = None
    metrics: dict[str, int | float | str | bool | None] | None = None


@dataclass(frozen=True)
class LearningEvidenceBundle:
    session: CompletedStudySession
    exercises: tuple[ExerciseAttemptEvidence, ...]
    performance: SkillPerformanceEvidence


@dataclass(frozen=True)
class RecordedLearningEvidence:
    study_session_id: int
    created: bool
