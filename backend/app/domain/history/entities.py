from dataclasses import dataclass
from datetime import date, datetime

from app.domain.learning_evidence.entities import Skill
from app.domain.study_plan.entities import DailyStudyPlan


@dataclass(frozen=True)
class HistoricalStudySession:
    id: int
    resource_id: int
    resource_title: str
    skill: Skill
    source_type: str
    source_id: str
    status: str
    started_at: datetime
    completed_at: datetime
    actual_duration_seconds: int | None
    accuracy: float | None
    attempt_count: int
    incorrect_item_count: int
    notes: str


@dataclass(frozen=True)
class StudyHistoryDay:
    study_date: date
    plan: DailyStudyPlan | None
    sessions: tuple[HistoricalStudySession, ...]

    @property
    def completed_module_count(self) -> int:
        if self.plan is None:
            return 0
        return sum(item.status.value == "completed" for item in self.plan.items)

    @property
    def assigned_module_count(self) -> int:
        return len(self.plan.items) if self.plan else 0
