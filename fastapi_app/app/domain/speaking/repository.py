from datetime import datetime
from typing import Protocol

from app.domain.speaking.entities import (
    RetellingDraft,
    RetellingRecord,
    RetellingSubmission,
    RetellingWorkspaceInput,
    ShadowingSentenceProgress,
    SpeakingPracticeStatus,
)


class SpeakingPracticeRepository(Protocol):
    def create(self, user_key: str, draft: RetellingDraft) -> RetellingRecord: ...

    def list_records(
        self,
        user_key: str,
        search: str,
        limit: int,
    ) -> tuple[RetellingRecord, ...]: ...

    def get_workspace_record(
        self,
        user_key: str,
        resource_id: int,
    ) -> RetellingRecord | None: ...

    def save_workspace_record(
        self,
        user_key: str,
        resource_id: int,
        prompt: str,
        source_context: str,
        draft_input: RetellingWorkspaceInput,
        occurred_at: datetime,
    ) -> RetellingRecord: ...

    def submit_workspace_record(
        self,
        user_key: str,
        resource_id: int,
        occurred_at: datetime,
    ) -> tuple[RetellingRecord, RetellingSubmission]: ...

    def list_sentence_progress(
        self,
        user_key: str,
        resource_id: int,
    ) -> tuple[ShadowingSentenceProgress, ...]: ...

    def save_sentence_progress(
        self,
        user_key: str,
        resource_id: int,
        sentence_key: str,
        practice_status: SpeakingPracticeStatus,
        occurred_at: datetime,
    ) -> ShadowingSentenceProgress: ...
