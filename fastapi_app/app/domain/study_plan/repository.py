from datetime import date
from typing import Protocol

from app.domain.study_plan.entities import (
    DailyStudyPlan,
    StudyPlanItemStatus,
    StudyPlanProposal,
    StudyPlanStatus,
)


class StudyPlanRepository(Protocol):
    def get_for_date(self, user_key: str, plan_date: date) -> DailyStudyPlan | None: ...

    def save(self, proposal: StudyPlanProposal) -> DailyStudyPlan: ...

    def set_item_status(
        self,
        user_key: str,
        plan_date: date,
        study_plan_item_id: int,
        status: StudyPlanItemStatus,
        plan_status: StudyPlanStatus,
    ) -> DailyStudyPlan: ...
