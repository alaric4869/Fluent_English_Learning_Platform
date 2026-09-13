from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class SpeakingPracticeStatus(StrEnum):
    NEED_PRACTICE = "need_practice"
    GOOD = "good"
    MASTERED = "mastered"


@dataclass(frozen=True)
class RetellingDraft:
    prompt: str
    written_outline: str = ""
    intended_vocabulary: tuple[str, ...] = ()
    mistakes: str = ""
    improved_version: str = ""
    practice_status: SpeakingPracticeStatus = SpeakingPracticeStatus.NEED_PRACTICE
    source_resource_id: int | None = None
    source_context: str = ""
    voice_recording_reference: str | None = None


@dataclass(frozen=True)
class RetellingRecord:
    id: int
    user_key: str
    prompt: str
    written_outline: str
    intended_vocabulary: tuple[str, ...]
    mistakes: str
    improved_version: str
    practice_status: SpeakingPracticeStatus
    source_resource_id: int | None
    source_context: str
    voice_recording_reference: str | None
    created_at: datetime
    updated_at: datetime
