from datetime import date, datetime

from pydantic import BaseModel, Field

from app.domain.learning_evidence.entities import Skill
from app.domain.study_plan.entities import StudyPlanItemStatus, StudyPlanStatus


class PlanItemOverrideRequest(BaseModel):
    planned_minutes: int
    resource_id: int | None
    note: str = Field(default="", max_length=500)


class PlanItemStatusRequest(BaseModel):
    status: StudyPlanItemStatus


class StudyPlanItemResponse(BaseModel):
    id: int
    skill: Skill
    system_planned_minutes: int
    planned_minutes: int
    system_resource_id: int | None
    resource_id: int | None
    status: StudyPlanItemStatus
    manual_override: bool
    started_at: datetime | None
    completed_at: datetime | None


class StudyPlanResponse(BaseModel):
    id: int
    plan_date: date
    status: StudyPlanStatus
    total_minutes: int
    items: list[StudyPlanItemResponse]
