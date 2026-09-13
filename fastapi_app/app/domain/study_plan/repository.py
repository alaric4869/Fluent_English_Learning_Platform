from datetime import date
from typing import Protocol

from app.domain.study_plan.entities import DailyStudyPlan, StudyPlanProposal


class StudyPlanRepository(Protocol):
    def get_for_date(self, user_key: str, plan_date: date) -> DailyStudyPlan | None: ...

    def save(self, proposal: StudyPlanProposal) -> DailyStudyPlan: ...
