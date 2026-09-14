from datetime import date

from app.domain.dashboard.entities import DashboardSnapshot
from app.services.progress_analytics import ProgressAnalyticsService
from app.services.review import ReviewService
from app.services.study_plan import StudyPlanService
from app.services.weekly_review import WeeklyReviewService


class DashboardService:
    def __init__(
        self,
        study_plan_service: StudyPlanService,
        progress_service: ProgressAnalyticsService,
        review_service: ReviewService,
        weekly_review_service: WeeklyReviewService,
    ) -> None:
        self.study_plan_service = study_plan_service
        self.progress_service = progress_service
        self.review_service = review_service
        self.weekly_review_service = weekly_review_service

    def get_snapshot(self, user_key: str, today: date) -> DashboardSnapshot:
        return DashboardSnapshot(
            today_plan=self.study_plan_service.get_or_create_daily_plan(
                user_key, today
            ),
            progress=self.progress_service.get_summary(user_key, today),
            due_review_count=self.review_service.get_due_count(user_key, today),
            weekly_review=self.weekly_review_service.get_current_week(user_key, today),
        )
