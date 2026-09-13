import math
from datetime import date, timedelta

from app.domain.review.config import DEFAULT_REVIEW_CONFIG, ReviewConfig
from app.domain.review.entities import (
    ReviewRating,
    ReviewScheduleResult,
    ReviewScheduleState,
)
from app.domain.vocabulary.entities import MasteryStatus


class FixedIntervalReviewScheduler:
    def __init__(self, config: ReviewConfig = DEFAULT_REVIEW_CONFIG) -> None:
        if not config.interval_days or any(day < 1 for day in config.interval_days):
            raise ValueError("review intervals must contain positive days")
        self.config = config

    @property
    def scheduler_version(self) -> str:
        return "fixed-interval-v1"

    def initial_state(self, learned_on: date) -> ReviewScheduleState:
        return ReviewScheduleState(
            step=0,
            next_review_date=learned_on + timedelta(days=self.config.interval_days[0]),
            mastery_status=MasteryStatus.NEW,
        )

    def schedule(
        self,
        current: ReviewScheduleState,
        rating: ReviewRating,
        reviewed_on: date,
    ) -> ReviewScheduleResult:
        current_step = min(max(current.step, 0), self.config.final_step)
        if rating is ReviewRating.AGAIN:
            next_step = 0
            interval_days = self.config.interval_days[0]
        elif rating is ReviewRating.HARD:
            next_step = current_step
            interval_days = max(
                1,
                math.ceil(self.config.interval_days[current_step] / 2),
            )
        else:
            increment = 2 if rating is ReviewRating.EASY else 1
            next_step = min(current_step + increment, self.config.final_step)
            interval_days = self.config.interval_days[next_step]

        return ReviewScheduleResult(
            state=ReviewScheduleState(
                step=next_step,
                next_review_date=reviewed_on + timedelta(days=interval_days),
                mastery_status=_mastery_for(rating, next_step, self.config.final_step),
            ),
            interval_days=interval_days,
        )


def _mastery_for(
    rating: ReviewRating,
    step: int,
    final_step: int,
) -> MasteryStatus:
    if rating is ReviewRating.AGAIN:
        return MasteryStatus.LEARNING
    if step >= final_step:
        return MasteryStatus.MASTERED
    if step >= 2:
        return MasteryStatus.FAMILIAR
    return MasteryStatus.LEARNING
