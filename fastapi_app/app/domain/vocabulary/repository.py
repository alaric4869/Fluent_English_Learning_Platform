from typing import Protocol

from app.domain.review.entities import ReviewScheduleState
from app.domain.vocabulary.entities import (
    MasteryStatus,
    VocabularyDifficulty,
    VocabularyDraft,
    VocabularyItem,
)


class VocabularyRepository(Protocol):
    def create(
        self,
        user_key: str,
        normalized_chunk: str,
        draft: VocabularyDraft,
        initial_schedule: ReviewScheduleState,
    ) -> VocabularyItem: ...

    def find_by_normalized_chunk(
        self,
        user_key: str,
        normalized_chunk: str,
    ) -> VocabularyItem | None: ...

    def get(self, user_key: str, vocabulary_item_id: int) -> VocabularyItem | None: ...

    def list_items(
        self,
        user_key: str,
        search: str,
        mastery_status: MasteryStatus | None,
        difficulty: VocabularyDifficulty | None,
        limit: int,
    ) -> tuple[VocabularyItem, ...]: ...

    def count_items(
        self,
        user_key: str,
        mastery_status: MasteryStatus | None = None,
    ) -> int: ...
