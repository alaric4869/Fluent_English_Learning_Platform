from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewConfig:
    interval_days: tuple[int, ...] = (1, 2, 4, 7, 16, 30)

    @property
    def final_step(self) -> int:
        return len(self.interval_days) - 1


DEFAULT_REVIEW_CONFIG = ReviewConfig()
