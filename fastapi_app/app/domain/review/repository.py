from datetime import date, datetime
from typing import Protocol

from app.domain.review.entities import RecordReviewCommand, RecordedReview, ReviewQueueItem


class ReviewRepository(Protocol):
    def list_due(
        self,
        user_key: str,
        due_on: date,
        limit: int,
    ) -> tuple[ReviewQueueItem, ...]: ...

    def count_due(self, user_key: str, due_on: date) -> int: ...

    def count_attempts_through(self, user_key: str, through: datetime) -> int: ...

    def get_item(self, user_key: str, review_item_id: int) -> ReviewQueueItem | None: ...

    def record(self, command: RecordReviewCommand) -> RecordedReview: ...
