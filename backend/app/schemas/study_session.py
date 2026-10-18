from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.learning_evidence.entities import Skill
from app.domain.study_session.entities import StudySessionStatus


class StudySessionProgressRequest(BaseModel):
    active_duration_seconds: int = Field(ge=0, le=28_800)
    notes: str = Field(default="", max_length=12_000)
    perceived_difficulty: int | None = Field(default=None, ge=1, le=5)
    confidence: int | None = Field(default=None, ge=1, le=5)


class ModuleStudySessionResponse(BaseModel):
    id: int
    study_plan_item_id: int
    resource_id: int
    skill: Skill
    revision: int
    status: StudySessionStatus
    started_at: datetime
    completed_at: datetime | None
    active_duration_seconds: int
    perceived_difficulty: int | None
    confidence: int | None
    notes: str
