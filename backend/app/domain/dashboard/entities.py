from dataclasses import dataclass

from app.domain.analytics.entities import ProgressSummary
from app.domain.study_plan.entities import DailyStudyPlan
from app.domain.weekly_review.entities import WeeklyReview


@dataclass(frozen=True)
class DashboardSnapshot:
    today_plan: DailyStudyPlan
    progress: ProgressSummary
    due_review_count: int
    weekly_review: WeeklyReview
