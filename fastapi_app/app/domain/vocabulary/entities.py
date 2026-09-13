from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum


class VocabularyDifficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class MasteryStatus(StrEnum):
    NEW = "new"
    LEARNING = "learning"
    FAMILIAR = "familiar"
    MASTERED = "mastered"


class DuplicateVocabularyError(ValueError):
    pass


@dataclass(frozen=True)
class VocabularyDraft:
    chunk: str
    meaning: str
    example_sentence: str
    learned_on: date
    personal_note: str
    difficulty: VocabularyDifficulty
    source_resource_id: int | None
    source_context: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class VocabularyItem:
    id: int
    user_key: str
    chunk: str
    meaning: str
    example_sentence: str
    learned_on: date
    personal_note: str
    difficulty: VocabularyDifficulty
    mastery_status: MasteryStatus
    source_resource_id: int | None
    source_context: str
    tags: tuple[str, ...]
    favorite: bool
    saved_for_later: bool
    review_item_id: int
    review_step: int
    next_review_date: date
    last_reviewed_at: datetime | None
    review_count: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class VocabularyLibrary:
    items: tuple[VocabularyItem, ...]
    total_count: int
    mastered_count: int
