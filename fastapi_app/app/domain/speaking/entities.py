from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.resources.entities import LearningResourceDetails


class SpeakingPracticeStatus(StrEnum):
    NEED_PRACTICE = "need_practice"
    GOOD = "good"
    MASTERED = "mastered"


class RetellingDraftStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"


@dataclass(frozen=True)
class RetellingWorkspaceInput:
    written_outline: str = ""
    intended_vocabulary: tuple[str, ...] = ()
    retelling_text: str = ""
    mistakes: str = ""
    improved_version: str = ""
    practice_status: SpeakingPracticeStatus = SpeakingPracticeStatus.NEED_PRACTICE
    active_duration_seconds: int = 0
    perceived_difficulty: int | None = None
    confidence: int | None = None


@dataclass(frozen=True)
class ShadowingSentenceProgress:
    id: int
    user_key: str
    resource_id: int
    sentence_key: str
    practice_status: SpeakingPracticeStatus
    practice_count: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class RetellingDraft:
    prompt: str
    written_outline: str = ""
    intended_vocabulary: tuple[str, ...] = ()
    retelling_text: str = ""
    mistakes: str = ""
    improved_version: str = ""
    practice_status: SpeakingPracticeStatus = SpeakingPracticeStatus.NEED_PRACTICE
    source_resource_id: int | None = None
    source_context: str = ""
    voice_recording_reference: str | None = None
    workspace_managed: bool = False
    active_duration_seconds: int = 0
    perceived_difficulty: int | None = None
    confidence: int | None = None


@dataclass(frozen=True)
class RetellingRecord:
    id: int
    user_key: str
    prompt: str
    written_outline: str
    intended_vocabulary: tuple[str, ...]
    retelling_text: str
    mistakes: str
    improved_version: str
    practice_status: SpeakingPracticeStatus
    source_resource_id: int | None
    source_context: str
    voice_recording_reference: str | None
    workspace_managed: bool
    active_duration_seconds: int
    perceived_difficulty: int | None
    confidence: int | None
    status: RetellingDraftStatus
    submission_revision: int
    started_at: datetime
    submitted_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class RetellingSubmission:
    id: int
    retelling_record_id: int
    revision: int
    written_outline_snapshot: str
    intended_vocabulary_snapshot: tuple[str, ...]
    retelling_text_snapshot: str
    mistakes_snapshot: str
    improved_version_snapshot: str
    practice_status: SpeakingPracticeStatus
    active_duration_seconds: int
    perceived_difficulty: int | None
    confidence: int | None
    submitted_at: datetime
    created: bool


@dataclass(frozen=True)
class ShadowingSentence:
    key: str
    speaker: str
    text: str
    pronunciation_note: str
    connected_speech_note: str
    chunks: tuple[str, ...]
    progress: ShadowingSentenceProgress | None = None


@dataclass(frozen=True)
class SpeakingWorkspace:
    resource: LearningResourceDetails
    record: RetellingRecord | None
    audio_url: str
    source_label: str
    context: str
    workflow: tuple[str, ...]
    sentences: tuple[ShadowingSentence, ...]
    retelling_prompt: str
    retelling_guidance: tuple[str, ...]
