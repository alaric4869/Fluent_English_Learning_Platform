from datetime import date
from typing import Protocol

from app.domain.review.entities import (
    ReviewRating,
    ReviewScheduleResult,
    ReviewScheduleState,
)


class ReviewScheduler(Protocol):
    @property
    def scheduler_version(self) -> str: ...

    def initial_state(self, learned_on: date) -> ReviewScheduleState: ...

    def schedule(
        self,
        current: ReviewScheduleState,
        rating: ReviewRating,
        reviewed_on: date,
    ) -> ReviewScheduleResult: ...
