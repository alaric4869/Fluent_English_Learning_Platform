from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.speaking.entities import RetellingDraftStatus, SpeakingPracticeStatus


class SpeakingDraftRequest(BaseModel):
    written_outline: str = Field(default="", max_length=12_000)
    intended_vocabulary: list[str] = Field(default_factory=list, max_length=40)
    retelling_text: str = Field(default="", max_length=20_000)
    mistakes: str = Field(default="", max_length=12_000)
    improved_version: str = Field(default="", max_length=20_000)
    practice_status: SpeakingPracticeStatus = SpeakingPracticeStatus.NEED_PRACTICE
    active_duration_seconds: int = Field(default=0, ge=0, le=28_800)
    perceived_difficulty: int | None = Field(default=None, ge=1, le=5)
    confidence: int | None = Field(default=None, ge=1, le=5)


class SpeakingDraftResponse(BaseModel):
    id: int
    resource_id: int
    written_outline: str
    intended_vocabulary: list[str]
    retelling_text: str
    mistakes: str
    improved_version: str
    practice_status: SpeakingPracticeStatus
    active_duration_seconds: int
    perceived_difficulty: int | None
    confidence: int | None
    status: RetellingDraftStatus
    submission_revision: int
    started_at: datetime
    submitted_at: datetime | None
    updated_at: datetime


class SpeakingSentenceStatusRequest(BaseModel):
    practice_status: SpeakingPracticeStatus


class SpeakingSentenceProgressResponse(BaseModel):
    id: int
    resource_id: int
    sentence_key: str
    practice_status: SpeakingPracticeStatus
    practice_count: int
    updated_at: datetime


class SpeakingSubmissionResponse(BaseModel):
    draft: SpeakingDraftResponse
    submission_id: int
    submission_revision: int
    study_session_id: int
    submitted_at: datetime
    created: bool
