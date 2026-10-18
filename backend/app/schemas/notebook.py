from datetime import date, datetime

from pydantic import BaseModel, Field

from app.domain.listening.entities import ListeningSentenceStatus
from app.domain.notebook.entities import NoteType
from app.domain.speaking.entities import SpeakingPracticeStatus
from app.domain.vocabulary.entities import MasteryStatus


class ListeningSentenceCreateRequest(BaseModel):
    sentence: str = Field(min_length=1, max_length=4000)
    meaning: str = Field(default="", max_length=4000)
    learned_on: date | None = None
    practice_status: ListeningSentenceStatus = ListeningSentenceStatus.DIFFICULT
    note: str = Field(default="", max_length=4000)
    source_resource_id: int | None = None
    source_context: str = Field(default="", max_length=1000)
    add_to_review: bool = True


class ListeningSentenceStatusRequest(BaseModel):
    practice_status: ListeningSentenceStatus


class ListeningSentenceResponse(BaseModel):
    id: int
    sentence: str
    meaning: str
    learned_on: date
    practice_status: ListeningSentenceStatus
    note: str
    source_context: str
    review_item_id: int | None
    next_review_date: date | None
    review_count: int
    mastery_status: MasteryStatus | None


class RetellingCreateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)
    written_outline: str = Field(default="", max_length=8000)
    intended_vocabulary: list[str] = Field(default_factory=list, max_length=40)
    mistakes: str = Field(default="", max_length=8000)
    improved_version: str = Field(default="", max_length=12000)
    practice_status: SpeakingPracticeStatus = SpeakingPracticeStatus.NEED_PRACTICE
    source_resource_id: int | None = None
    source_context: str = Field(default="", max_length=1000)


class RetellingResponse(BaseModel):
    id: int
    prompt: str
    written_outline: str
    intended_vocabulary: list[str]
    mistakes: str
    improved_version: str
    practice_status: SpeakingPracticeStatus
    source_context: str
    voice_recording_reference: str | None
    created_at: datetime


class NotebookNoteCreateRequest(BaseModel):
    note_type: NoteType
    title: str = Field(min_length=1, max_length=300)
    content: str = Field(min_length=1, max_length=12000)
    source_resource_id: int | None = None
    source_context: str = Field(default="", max_length=1000)
    tags: list[str] = Field(default_factory=list, max_length=30)


class NotebookNoteResponse(BaseModel):
    id: int
    note_type: NoteType
    title: str
    content: str
    source_context: str
    tags: list[str]
    favorite: bool
    saved_for_later: bool
    created_at: datetime
