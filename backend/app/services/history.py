from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from app.domain.history.entities import HistoricalStudySession, StudyHistoryDay
from app.domain.history.repository import StudyHistoryRepository
from app.domain.study_plan.repository import StudyPlanRepository


class HistoryService:
    def __init__(
        self,
        study_plan_repository: StudyPlanRepository,
        history_repository: StudyHistoryRepository,
        timezone: ZoneInfo,
    ) -> None:
        self.study_plan_repository = study_plan_repository
        self.history_repository = history_repository
        self.timezone = timezone

    def list_recent_days(
        self,
        user_key: str,
        through_date: date,
        limit: int = 90,
    ) -> tuple[StudyHistoryDay, ...]:
        if limit < 1:
            raise ValueError("limit must be positive")
        plans = self.study_plan_repository.list_recent(user_key, through_date, limit)
        sessions = self.history_repository.list_recent_sessions(
            user_key,
            self._day_boundary(through_date + timedelta(days=1)),
            limit * 10,
        )
        return self._group_days(plans, sessions)[:limit]

    def get_day(self, user_key: str, study_date: date) -> StudyHistoryDay | None:
        plan = self.study_plan_repository.get_for_date(user_key, study_date)
        sessions = self.history_repository.list_sessions_between(
            user_key,
            self._day_boundary(study_date),
            self._day_boundary(study_date + timedelta(days=1)),
        )
        if plan is None and not sessions:
            return None
        return StudyHistoryDay(study_date, plan, sessions)

    def list_month(
        self,
        user_key: str,
        month: date,
    ) -> tuple[StudyHistoryDay, ...]:
        start = month.replace(day=1)
        end = _next_month(start)
        plans = self.study_plan_repository.list_between(user_key, start, end)
        sessions = self.history_repository.list_sessions_between(
            user_key,
            self._day_boundary(start),
            self._day_boundary(end),
        )
        return self._group_days(plans, sessions)

    def _group_days(
        self,
        plans,
        sessions: tuple[HistoricalStudySession, ...],
    ) -> tuple[StudyHistoryDay, ...]:
        plans_by_date = {plan.plan_date: plan for plan in plans}
        sessions_by_date: dict[date, list[HistoricalStudySession]] = {}
        for session in sessions:
            local_date = _as_aware(session.completed_at).astimezone(self.timezone).date()
            sessions_by_date.setdefault(local_date, []).append(session)
        dates = sorted(set(plans_by_date) | set(sessions_by_date), reverse=True)
        return tuple(
            StudyHistoryDay(
                study_date=value,
                plan=plans_by_date.get(value),
                sessions=tuple(sessions_by_date.get(value, [])),
            )
            for value in dates
        )

    def _day_boundary(self, value: date) -> datetime:
        return datetime.combine(value, time.min, tzinfo=self.timezone).astimezone(
            timezone.utc
        )


def _as_aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=ZoneInfo("UTC"))


def _next_month(value: date) -> date:
    return (value.replace(day=28) + timedelta(days=4)).replace(day=1)
