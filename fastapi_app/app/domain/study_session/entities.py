from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.learning_evidence.entities import Skill


class StudySessionStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass(frozen=True)
class StudySessionProgress:
    active_duration_seconds: int
    notes: str
    perceived_difficulty: int | None
    confidence: int | None


@dataclass(frozen=True)
class StartModuleSessionCommand:
    user_key: str
    study_plan_item_id: int
    resource_id: int
    skill: Skill
    started_at: datetime


@dataclass(frozen=True)
class SaveModuleSessionCommand:
    user_key: str
    study_plan_item_id: int
    study_session_id: int
    progress: StudySessionProgress
    occurred_at: datetime


@dataclass(frozen=True)
class ModuleStudySession:
    id: int
    user_key: str
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
    created_at: datetime
    updated_at: datetime
