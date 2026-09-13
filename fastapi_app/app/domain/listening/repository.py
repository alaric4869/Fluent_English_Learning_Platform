from typing import Protocol

from app.domain.listening.entities import (
    ListeningSentenceDraft,
    ListeningSentenceStatus,
    SavedListeningSentence,
)
from app.domain.review.entities import ReviewScheduleState


class ListeningSentenceRepository(Protocol):
    def create(
        self,
        user_key: str,
        draft: ListeningSentenceDraft,
        initial_schedule: ReviewScheduleState | None,
    ) -> SavedListeningSentence: ...

    def get(self, user_key: str, sentence_id: int) -> SavedListeningSentence | None: ...

    def list_items(
        self,
        user_key: str,
        search: str,
        status: ListeningSentenceStatus | None,
        limit: int,
    ) -> tuple[SavedListeningSentence, ...]: ...

    def update_status(
        self,
        user_key: str,
        sentence_id: int,
        status: ListeningSentenceStatus,
    ) -> SavedListeningSentence | None: ...
