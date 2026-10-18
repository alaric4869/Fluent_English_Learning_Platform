from datetime import datetime
from typing import Literal

from pydantic import BaseModel



class WritingDraftStateResponse(BaseModel):
    id: int | None
    resource_id: int
    response_text: str
    outline: str
    word_count: int
    active_duration_seconds: int
    perceived_difficulty: int | None
    confidence: int | None
    status: str
    submission_revision: int
    started_at: datetime | None
    submitted_at: datetime | None
    updated_at: datetime | None


class WritingWorkspaceResponse(BaseModel):
    resource_id: int
    resource_title: str
    description: str
    test_number: int
    minimum_words: int
    recommended_minutes: int
    task_type: str
    instructions: str
    situation: str
    prompt: str
    bullet_points: list[str]
    closing_instruction: str
    draft: WritingDraftStateResponse


class SpeakingSentenceProgressStateResponse(BaseModel):
    practice_status: str
    practice_count: int
    updated_at: datetime


class SpeakingSentenceResponse(BaseModel):
    key: str
    speaker: str
    text: str
    pronunciation_note: str
    connected_speech_note: str
    chunks: list[str]
    progress: SpeakingSentenceProgressStateResponse | None


class SpeakingDraftStateResponse(BaseModel):
    id: int | None
    resource_id: int
    written_outline: str
    intended_vocabulary: list[str]
    retelling_text: str
    mistakes: str
    improved_version: str
    practice_status: str
    active_duration_seconds: int
    perceived_difficulty: int | None
    confidence: int | None
    status: str
    submission_revision: int
    started_at: datetime | None
    submitted_at: datetime | None
    updated_at: datetime | None


class SpeakingWorkspaceResponse(BaseModel):
    resource_id: int
    resource_title: str
    description: str
    test_number: int
    estimated_duration_minutes: int
    audio_url: str
    source_label: str
    context: str
    workflow: list[str]
    sentences: list[SpeakingSentenceResponse]
    retelling_prompt: str
    retelling_guidance: list[str]
    marked_count: int
    mastered_count: int
    draft: SpeakingDraftStateResponse


class ListeningAudioPartResponse(BaseModel):
    number: int
    label: str
    url: str


class ListeningSentenceResponse(BaseModel):
    position: int
    text: str
    status: str
    saved_id: int | None
    review_item_id: int | None
    next_review_date: str | None


class ListeningWorkspaceResponse(BaseModel):
    resource_id: int
    title: str
    description: str
    topic: str
    difficulty: str | None
    resource_type: str
    estimated_duration_minutes: int
    is_user_owned: bool
    media_kind: Literal["youtube", "audio", "local_parts", "external", "missing"]
    media_url: str | None
    local_audio_parts: list[ListeningAudioPartResponse]
    practice_href: str | None
    sentences: list[ListeningSentenceResponse]
