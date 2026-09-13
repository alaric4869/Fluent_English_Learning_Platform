from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from app.domain.analytics.entities import (
    DailyActivity,
    ProgressSummary,
    SkillProgressSummary,
)
from app.domain.analytics.streaks import calculate_streaks
from app.domain.history.repository import StudyHistoryRepository
from app.domain.learning_evidence.entities import Skill
from app.domain.learner_profile.entities import EvidenceStatus
from app.domain.review.repository import ReviewRepository
from app.domain.study_plan.entities import StudyPlanItemStatus
from app.domain.study_plan.repository import StudyPlanRepository
from app.domain.weakness_detection.entities import SkillClassification
from app.services.learner_profile import LearnerProfileService
from app.services.weakness_detection import WeaknessDetectionService


class ProgressAnalyticsService:
    def __init__(
        self,
        study_plan_repository: StudyPlanRepository,
        history_repository: StudyHistoryRepository,
        learner_profile_service: LearnerProfileService,
        weakness_detection_service: WeaknessDetectionService,
        review_repository: ReviewRepository,
        timezone: ZoneInfo,
    ) -> None:
        self.study_plan_repository = study_plan_repository
        self.history_repository = history_repository
        self.learner_profile_service = learner_profile_service
        self.weakness_detection_service = weakness_detection_service
        self.review_repository = review_repository
        self.timezone = timezone

    def get_summary(self, user_key: str, today: date) -> ProgressSummary:
        plans = self.study_plan_repository.list_all_through(user_key, today)
        sessions = self.history_repository.list_all_sessions_through(
            user_key,
            self._day_boundary(today + timedelta(days=1)),
        )
        profile = self.learner_profile_service.get_current_profile(user_key)
        assessment = self.weakness_detection_service.get_current_assessment(user_key)

        assigned_modules = sum(len(plan.items) for plan in plans)
        completed_items = tuple(
            item
            for plan in plans
            for item in plan.items
            if item.status is StudyPlanItemStatus.COMPLETED
        )
        session_dates = {
            _as_aware(item.completed_at).astimezone(self.timezone).date()
            for item in sessions
        }
        plan_activity_dates = {
            plan.plan_date
            for plan in plans
            if any(
                item.status is StudyPlanItemStatus.COMPLETED for item in plan.items
            )
        }
        activity_dates = tuple(plan_activity_dates | session_dates)
        current_streak, longest_streak = calculate_streaks(activity_dates, today)
        recent_activity = self._build_recent_activity(plans, sessions, today)
        week_start = today - timedelta(days=today.weekday())

        profiles_by_skill = (
            {item.skill: item for item in profile.skills} if profile else {}
        )
        assessments_by_skill = (
            {item.skill: item for item in assessment.skills} if assessment else {}
        )
        skill_summaries = tuple(
            SkillProgressSummary(
                skill=skill,
                completed_modules=sum(
                    item.skill is skill for item in completed_items
                ),
                completed_sessions=sum(item.skill is skill for item in sessions),
                profile_score=(
                    profiles_by_skill[skill].score
                    if skill in profiles_by_skill
                    else None
                ),
                evidence_status=(
                    profiles_by_skill[skill].evidence_status
                    if skill in profiles_by_skill
                    else EvidenceStatus.NO_DATA
                ),
                classification=(
                    assessments_by_skill[skill].classification
                    if skill in assessments_by_skill
                    else SkillClassification.INSUFFICIENT_EVIDENCE
                ),
            )
            for skill in Skill
        )

        return ProgressSummary(
            current_streak=current_streak,
            longest_streak=longest_streak,
            total_study_days=len(activity_dates),
            assigned_modules=assigned_modules,
            completed_modules=len(completed_items),
            completion_rate=(
                round(len(completed_items) / assigned_modules * 100, 1)
                if assigned_modules
                else 0.0
            ),
            completed_planned_minutes=sum(
                item.planned_minutes for item in completed_items
            ),
            tracked_seconds=sum(
                item.actual_duration_seconds or 0 for item in sessions
            ),
            this_week_completed_planned_minutes=sum(
                item.completed_planned_minutes
                for item in recent_activity
                if item.activity_date >= week_start
            ),
            completed_sessions=len(sessions),
            completed_reviews=self.review_repository.count_attempts_through(
                user_key,
                self._day_boundary(today + timedelta(days=1)),
            ),
            skill_summaries=skill_summaries,
            recent_activity=recent_activity,
        )

    def _build_recent_activity(self, plans, sessions, today: date):
        start = today - timedelta(days=27)
        plans_by_date = {plan.plan_date: plan for plan in plans}
        sessions_by_date = {}
        for session in sessions:
            local_date = _as_aware(session.completed_at).astimezone(self.timezone).date()
            if start <= local_date <= today:
                sessions_by_date.setdefault(local_date, []).append(session)

        activity = []
        for offset in range(28):
            activity_date = start + timedelta(days=offset)
            plan = plans_by_date.get(activity_date)
            completed_items = tuple(
                item
                for item in plan.items
                if item.status is StudyPlanItemStatus.COMPLETED
            ) if plan else ()
            day_sessions = sessions_by_date.get(activity_date, [])
            activity.append(
                DailyActivity(
                    activity_date=activity_date,
                    assigned_modules=len(plan.items) if plan else 0,
                    completed_modules=len(completed_items),
                    completed_planned_minutes=sum(
                        item.planned_minutes for item in completed_items
                    ),
                    completed_sessions=len(day_sessions),
                    tracked_seconds=sum(
                        item.actual_duration_seconds or 0 for item in day_sessions
                    ),
                )
            )
        return tuple(activity)

    def _day_boundary(self, value: date) -> datetime:
        return datetime.combine(value, time.min, tzinfo=self.timezone).astimezone(
            timezone.utc
        )


def _as_aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=ZoneInfo("UTC"))
