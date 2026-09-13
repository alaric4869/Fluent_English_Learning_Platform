from typing import Protocol

from app.domain.speaking.entities import RetellingDraft, RetellingRecord


class SpeakingPracticeRepository(Protocol):
    def create(self, user_key: str, draft: RetellingDraft) -> RetellingRecord: ...

    def list_records(
        self,
        user_key: str,
        search: str,
        limit: int,
    ) -> tuple[RetellingRecord, ...]: ...
