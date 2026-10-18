from dataclasses import dataclass
from datetime import date

from app.domain.learning_evidence.entities import Skill
from app.domain.review.entities import ReviewAttemptSummary


@dataclass(frozen=True)
class WeeklySkillSummary:
    skill: Skill
    completed_modules: int
    completed_sessions: int
    average_accuracy: float | None
    incorrect_item_count: int
    tracked_seconds: int


@dataclass(frozen=True)
class WeeklyReviewRecommendation:
    title: str
    reason: str
    href: str


@dataclass(frozen=True)
class WeeklyReview:
    week_start: date
    week_end: date
    study_days: int
    assigned_modules: int
    completed_modules: int
    completion_rate: float
    completed_planned_minutes: int
    completed_sessions: int
    tracked_seconds: int
    vocabulary_learned: int
    difficult_sentences_collected: int
    review_attempts: ReviewAttemptSummary
    next_week_review_count: int
    strongest_skill: Skill | None
    weakest_skill: Skill | None
    skill_summaries: tuple[WeeklySkillSummary, ...]
    recommendations: tuple[WeeklyReviewRecommendation, ...]
