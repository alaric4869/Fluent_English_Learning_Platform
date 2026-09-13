from collections.abc import Callable
from datetime import date, datetime, timezone

from app.domain.review.entities import (
    RecordReviewCommand,
    RecordedReview,
    ReviewRating,
    ReviewScheduleState,
)
from app.domain.review.repository import ReviewRepository
from app.domain.review.scheduler import ReviewScheduler
from app.domain.vocabulary.entities import VocabularyItem


class ReviewService:
    def __init__(
        self,
        repository: ReviewRepository,
        scheduler: ReviewScheduler,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.repository = repository
        self.scheduler = scheduler
        self.now = now or utc_now

    def get_due_reviews(
        self,
        user_key: str,
        due_on: date,
        limit: int = 50,
    ) -> tuple[VocabularyItem, ...]:
        if limit < 1 or limit > 200:
            raise ValueError("limit must be between 1 and 200")
        return self.repository.list_due(user_key, due_on, limit)

    def get_due_count(self, user_key: str, due_on: date) -> int:
        return self.repository.count_due(user_key, due_on)

    def record_review(
        self,
        user_key: str,
        review_item_id: int,
        rating: ReviewRating,
        reviewed_on: date,
        request_id: str,
    ) -> RecordedReview:
        item = self.repository.get_item(user_key, review_item_id)
        if item is None:
            raise LookupError("Review item not found")
        previous_state = ReviewScheduleState(
            step=item.review_step,
            next_review_date=item.next_review_date,
            mastery_status=item.mastery_status,
        )
        result = self.scheduler.schedule(previous_state, rating, reviewed_on)
        return self.repository.record(
            RecordReviewCommand(
                user_key=user_key,
                review_item_id=review_item_id,
                request_id=request_id,
                rating=rating,
                reviewed_at=self.now(),
                previous_state=previous_state,
                result=result,
            )
        )


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
