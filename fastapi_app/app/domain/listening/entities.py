from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum

from app.domain.vocabulary.entities import MasteryStatus


class ListeningSentenceStatus(StrEnum):
    COULD_NOT_HEAR = "could_not_hear"
    DIFFICULT = "difficult"
    UNDERSTOOD = "understood"
    MASTERED = "mastered"


@dataclass(frozen=True)
class ListeningSentenceDraft:
    sentence: str
    meaning: str
    learned_on: date
    practice_status: ListeningSentenceStatus
    note: str = ""
    source_resource_id: int | None = None
    source_context: str = ""
    add_to_review: bool = True


@dataclass(frozen=True)
class SavedListeningSentence:
    id: int
    user_key: str
    sentence: str
    meaning: str
    learned_on: date
    practice_status: ListeningSentenceStatus
    note: str
    source_resource_id: int | None
    source_context: str
    favorite: bool
    saved_for_later: bool
    review_item_id: int | None
    review_step: int | None
    next_review_date: date | None
    last_reviewed_at: datetime | None
    review_count: int
    mastery_status: MasteryStatus | None
    created_at: datetime
    updated_at: datetime
