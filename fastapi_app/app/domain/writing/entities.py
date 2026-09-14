from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.resources.entities import LearningResourceDetails


class WritingDraftStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"


@dataclass(frozen=True)
class WritingDraftInput:
    response_text: str
    outline: str
    active_duration_seconds: int
    perceived_difficulty: int | None = None
    confidence: int | None = None


@dataclass(frozen=True)
class WritingDraft:
    id: int
    user_key: str
    resource_id: int
    response_text: str
    outline: str
    word_count: int
    active_duration_seconds: int
    perceived_difficulty: int | None
    confidence: int | None
    status: WritingDraftStatus
    submission_revision: int
    started_at: datetime
    submitted_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class WritingSubmission:
    id: int
    writing_draft_id: int
    revision: int
    response_snapshot: str
    outline_snapshot: str
    word_count: int
    active_duration_seconds: int
    perceived_difficulty: int | None
    confidence: int | None
    submitted_at: datetime
    created: bool


@dataclass(frozen=True)
class WritingWorkspace:
    resource: LearningResourceDetails
    draft: WritingDraft | None
    minimum_words: int
    recommended_minutes: int
    task_type: str
    instructions: str
    situation: str
    prompt: str
    bullet_points: tuple[str, ...]
    closing_instruction: str
