from datetime import date

from app.domain.resources.repository import ResourceRepository
from app.domain.review.scheduler import ReviewScheduler
from app.domain.vocabulary.entities import (
    DuplicateVocabularyError,
    MasteryStatus,
    VocabularyDifficulty,
    VocabularyDraft,
    VocabularyItem,
    VocabularyLibrary,
)
from app.domain.vocabulary.repository import VocabularyRepository


class InvalidVocabularyError(ValueError):
    pass


class VocabularyService:
    def __init__(
        self,
        repository: VocabularyRepository,
        resource_repository: ResourceRepository,
        review_scheduler: ReviewScheduler,
    ) -> None:
        self.repository = repository
        self.resource_repository = resource_repository
        self.review_scheduler = review_scheduler

    def add_item(
        self,
        user_key: str,
        draft: VocabularyDraft,
        today: date,
    ) -> VocabularyItem:
        normalized_draft = _normalize_draft(draft)
        if normalized_draft.learned_on > today:
            raise InvalidVocabularyError("Learned date cannot be in the future")
        if normalized_draft.source_resource_id is not None and self.resource_repository.get(
            normalized_draft.source_resource_id
        ) is None:
            raise InvalidVocabularyError("Source resource not found")
        normalized_chunk = _normalize_chunk(normalized_draft.chunk)
        if self.repository.find_by_normalized_chunk(user_key, normalized_chunk):
            raise DuplicateVocabularyError("This vocabulary chunk already exists")
        initial_schedule = self.review_scheduler.initial_state(
            normalized_draft.learned_on
        )
        return self.repository.create(
            user_key,
            normalized_chunk,
            normalized_draft,
            initial_schedule,
        )

    def get_library(
        self,
        user_key: str,
        search: str = "",
        mastery_status: MasteryStatus | None = None,
        difficulty: VocabularyDifficulty | None = None,
        limit: int = 200,
    ) -> VocabularyLibrary:
        if limit < 1 or limit > 500:
            raise ValueError("limit must be between 1 and 500")
        return VocabularyLibrary(
            items=self.repository.list_items(
                user_key,
                search.strip(),
                mastery_status,
                difficulty,
                limit,
            ),
            total_count=self.repository.count_items(user_key),
            mastered_count=self.repository.count_items(
                user_key,
                MasteryStatus.MASTERED,
            ),
        )


def _normalize_draft(draft: VocabularyDraft) -> VocabularyDraft:
    chunk = " ".join(draft.chunk.split())
    meaning = " ".join(draft.meaning.split())
    if not chunk:
        raise InvalidVocabularyError("Vocabulary chunk is required")
    if not meaning:
        raise InvalidVocabularyError("Meaning is required")
    return VocabularyDraft(
        chunk=chunk,
        meaning=meaning,
        example_sentence=draft.example_sentence.strip(),
        learned_on=draft.learned_on,
        personal_note=draft.personal_note.strip(),
        difficulty=draft.difficulty,
        source_resource_id=draft.source_resource_id,
        source_context=draft.source_context.strip(),
        tags=_normalize_tags(draft.tags),
    )


def _normalize_chunk(value: str) -> str:
    return " ".join(value.casefold().split())


def _normalize_tags(values: tuple[str, ...]) -> tuple[str, ...]:
    unique: list[str] = []
    seen: set[str] = set()
    for value in values:
        tag = " ".join(value.split())
        key = tag.casefold()
        if tag and key not in seen:
            unique.append(tag)
            seen.add(key)
    return tuple(unique)
