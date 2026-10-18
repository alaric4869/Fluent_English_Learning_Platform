from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.writing.entities import WritingDraftStatus


class WritingDraftRequest(BaseModel):
    response_text: str = Field(default="", max_length=30_000)
    outline: str = Field(default="", max_length=12_000)
    active_duration_seconds: int = Field(default=0, ge=0, le=28_800)
    perceived_difficulty: int | None = Field(default=None, ge=1, le=5)
    confidence: int | None = Field(default=None, ge=1, le=5)


class WritingDraftResponse(BaseModel):
    id: int
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
    updated_at: datetime


class WritingSubmissionResponse(BaseModel):
    draft: WritingDraftResponse
    submission_id: int
    submission_revision: int
    study_session_id: int
    word_count: int
    submitted_at: datetime
    created: bool
