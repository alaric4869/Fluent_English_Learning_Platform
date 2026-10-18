from datetime import date, datetime

from pydantic import BaseModel


class NotebookNoteItemResponse(BaseModel):
    id: int
    note_type: str
    type_label: str
    title: str
    content: str
    source_context: str
    tags: list[str]
    favorite: bool
    saved_for_later: bool
    created_at: datetime


class NotebookSentenceItemResponse(BaseModel):
    id: int
    sentence: str
    meaning: str
    learned_on: date
    practice_status: str
    status_label: str
    note: str
    source_context: str
    review_item_id: int | None
    next_review_date: date | None
    review_count: int
    mastery_status: str | None


class NotebookRetellingItemResponse(BaseModel):
    id: int
    prompt: str
    written_outline: str
    intended_vocabulary: list[str]
    retelling_text: str
    mistakes: str
    improved_version: str
    practice_status: str
    status_label: str
    source_context: str
    created_at: datetime


class NotebookCountsResponse(BaseModel):
    notes: int
    sentences: int
    retellings: int


class NotebookResponse(BaseModel):
    counts: NotebookCountsResponse
    notes: list[NotebookNoteItemResponse]
    sentences: list[NotebookSentenceItemResponse]
    retellings: list[NotebookRetellingItemResponse]
