from datetime import date, datetime
from typing import Protocol

from app.domain.study_plan.entities import (
    DailyStudyPlan,
    StudyPlanItemStatus,
    StudyPlanProposal,
    StudyPlanStatus,
)


class StudyPlanRepository(Protocol):
    def get_for_date(self, user_key: str, plan_date: date) -> DailyStudyPlan | None: ...

    def list_recent(
        self,
        user_key: str,
        through_date: date,
        limit: int,
    ) -> tuple[DailyStudyPlan, ...]: ...

    def list_all_through(
        self,
        user_key: str,
        through_date: date,
    ) -> tuple[DailyStudyPlan, ...]: ...

    def list_between(
        self,
        user_key: str,
        start_date: date,
        end_date: date,
    ) -> tuple[DailyStudyPlan, ...]: ...

    def save(self, proposal: StudyPlanProposal) -> DailyStudyPlan: ...

    def set_item_status(
        self,
        user_key: str,
        plan_date: date,
        study_plan_item_id: int,
        status: StudyPlanItemStatus,
        plan_status: StudyPlanStatus,
        started_at: datetime | None,
        completed_at: datetime | None,
    ) -> DailyStudyPlan: ...
