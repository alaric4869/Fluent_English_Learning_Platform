from datetime import date, datetime
from typing import Protocol

from app.domain.review.entities import (
    RecordReviewCommand,
    RecordedReview,
    ReviewAttemptSummary,
    ReviewQueueItem,
)


class ReviewRepository(Protocol):
    def list_due(
        self,
        user_key: str,
        due_on: date,
        limit: int,
    ) -> tuple[ReviewQueueItem, ...]: ...

    def count_due(self, user_key: str, due_on: date) -> int: ...

    def count_attempts_through(self, user_key: str, through: datetime) -> int: ...

    def summarize_attempts_between(
        self,
        user_key: str,
        start: datetime,
        end: datetime,
    ) -> ReviewAttemptSummary: ...

    def count_active_scheduled_between(
        self,
        user_key: str,
        start_date: date,
        end_date: date,
    ) -> int: ...

    def get_item(self, user_key: str, review_item_id: int) -> ReviewQueueItem | None: ...

    def record(self, command: RecordReviewCommand) -> RecordedReview: ...
