from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class NoteType(StrEnum):
    VOCABULARY = "vocabulary"
    USEFUL_EXPRESSION = "useful_expression"
    LISTENING_MISTAKE = "listening_mistake"
    PRONUNCIATION = "pronunciation"
    GRAMMAR = "grammar"
    SPEAKING_MISTAKE = "speaking_mistake"
    SENTENCE = "sentence"


@dataclass(frozen=True)
class NoteDraft:
    note_type: NoteType
    title: str
    content: str
    source_resource_id: int | None = None
    source_context: str = ""
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class NotebookNote:
    id: int
    user_key: str
    note_type: NoteType
    title: str
    content: str
    source_resource_id: int | None
    source_context: str
    tags: tuple[str, ...]
    favorite: bool
    saved_for_later: bool
    created_at: datetime
    updated_at: datetime
