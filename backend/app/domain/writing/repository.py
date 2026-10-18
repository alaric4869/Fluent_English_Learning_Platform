from datetime import datetime
from typing import Protocol

from app.domain.writing.entities import (
    WritingDraft,
    WritingDraftInput,
    WritingSubmission,
)


class WritingRepository(Protocol):
    def get_draft(self, user_key: str, resource_id: int) -> WritingDraft | None: ...

    def save_draft(
        self,
        user_key: str,
        resource_id: int,
        draft_input: WritingDraftInput,
        word_count: int,
        occurred_at: datetime,
    ) -> WritingDraft: ...

    def submit(
        self,
        user_key: str,
        resource_id: int,
        occurred_at: datetime,
    ) -> tuple[WritingDraft, WritingSubmission]: ...

    def get_submission(
        self,
        user_key: str,
        resource_id: int,
        revision: int | None = None,
    ) -> WritingSubmission | None: ...
