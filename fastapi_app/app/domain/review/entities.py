from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum

from app.domain.vocabulary.entities import MasteryStatus


class ReviewRating(StrEnum):
    AGAIN = "again"
    HARD = "hard"
    GOOD = "good"
    EASY = "easy"


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
class RecordedReview:
    review_attempt_id: int
    vocabulary_item_id: int
    review_item_id: int
    mastery_status: MasteryStatus
    next_review_date: date
    review_count: int
    created: bool
