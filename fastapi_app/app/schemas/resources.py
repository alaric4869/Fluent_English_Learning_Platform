from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.learning_evidence.entities import Skill


class ResourceUpsertRequest(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    resource_type: str = Field(min_length=1, max_length=60)
    skill: Skill
    topic: str = Field(min_length=1, max_length=120)
    difficulty: str | None = Field(default=None, max_length=40)
    estimated_duration_minutes: int = Field(ge=1, le=300)
    source_url: str | None = Field(default=None, max_length=500)
    description: str = Field(default="", max_length=4000)
    content_text: str = Field(default="", max_length=100_000)
    transcript: str = Field(default="", max_length=100_000)
    notes: str = Field(default="", max_length=12_000)
    tags: list[str] = Field(default_factory=list, max_length=40)
    priority: int = Field(default=50, ge=0, le=100)


class ResourceStateRequest(BaseModel):
    favorite: bool | None = None
    saved_for_later: bool | None = None
    archived: bool | None = None


class ResourceResponse(BaseModel):
    id: int
    title: str
    resource_type: str
    skill: Skill
    topic: str
    difficulty: str | None
    estimated_duration_minutes: int
    source_url: str | None
    description: str
    content_text: str
    transcript: str
    notes: str
    tags: list[str]
    priority: int
    favorite: bool
    saved_for_later: bool
    archived: bool
    is_user_owned: bool
    last_studied_at: datetime | None
    completed_session_count: int
