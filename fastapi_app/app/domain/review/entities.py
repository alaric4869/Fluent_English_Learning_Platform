from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum

from app.domain.vocabulary.entities import MasteryStatus


class ReviewRating(StrEnum):
    AGAIN = "again"
    HARD = "hard"
    GOOD = "good"
    EASY = "easy"


class ReviewTargetType(StrEnum):
    VOCABULARY = "vocabulary"
    SAVED_SENTENCE = "saved_sentence"


class ReviewConflictError(RuntimeError):
    pass


@dataclass(frozen=True)
class ReviewScheduleState:
    step: int
    next_review_date: date
    mastery_status: MasteryStatus


@dataclass(frozen=True)
class ReviewScheduleResult:
    state: ReviewScheduleState
    interval_days: int


@dataclass(frozen=True)
class RecordReviewCommand:
    user_key: str
    review_item_id: int
    request_id: str
    rating: ReviewRating
    reviewed_at: datetime
    previous_state: ReviewScheduleState
    result: ReviewScheduleResult


@dataclass(frozen=True)
class ReviewQueueItem:
    review_item_id: int
    user_key: str
    target_type: ReviewTargetType
    target_id: int
    scheduler_version: str
    review_step: int
    next_review_date: date
    last_reviewed_at: datetime | None
    review_count: int
    mastery_status: MasteryStatus

    @property
    def id(self) -> int:
        """Backward-compatible target ID for existing vocabulary callers."""
        return self.target_id


@dataclass(frozen=True)
class RecordedReview:
    review_attempt_id: int
    target_type: ReviewTargetType
    target_id: int
    vocabulary_item_id: int | None
    saved_sentence_id: int | None
    review_item_id: int
    mastery_status: MasteryStatus
    next_review_date: date
    review_count: int
    created: bool
