from datetime import date

from app.domain.listening.entities import (
    ListeningSentenceDraft,
    ListeningSentenceStatus,
    SavedListeningSentence,
)
from app.domain.listening.repository import ListeningSentenceRepository
from app.domain.resources.repository import ResourceRepository
from app.domain.review.scheduler import ReviewScheduler


class InvalidListeningSentenceError(ValueError):
    pass


class ListeningPracticeService:
    def __init__(
        self,
        repository: ListeningSentenceRepository,
        resource_repository: ResourceRepository,
        review_scheduler: ReviewScheduler,
    ) -> None:
        self.repository = repository
        self.resource_repository = resource_repository
        self.review_scheduler = review_scheduler

    def save_sentence(
        self,
        user_key: str,
        draft: ListeningSentenceDraft,
        today: date,
    ) -> SavedListeningSentence:
        normalized = _normalize_draft(draft)
        if normalized.learned_on > today:
            raise InvalidListeningSentenceError("Learned date cannot be in the future")
        self._validate_resource(normalized.source_resource_id)
        initial_schedule = (
            self.review_scheduler.initial_state(normalized.learned_on)
            if normalized.add_to_review
            else None
        )
        return self.repository.create(user_key, normalized, initial_schedule)

    def get_sentence(
        self, user_key: str, sentence_id: int
    ) -> SavedListeningSentence | None:
        return self.repository.get(user_key, sentence_id)

    def list_sentences(
        self,
        user_key: str,
        search: str = "",
        status: ListeningSentenceStatus | None = None,
        limit: int = 200,
    ) -> tuple[SavedListeningSentence, ...]:
        if limit < 1 or limit > 500:
            raise ValueError("limit must be between 1 and 500")
        return self.repository.list_items(user_key, search.strip(), status, limit)

    def update_status(
        self,
        user_key: str,
        sentence_id: int,
        status: ListeningSentenceStatus,
    ) -> SavedListeningSentence:
        item = self.repository.update_status(user_key, sentence_id, status)
        if item is None:
            raise LookupError("Saved sentence not found")
        return item

    def _validate_resource(self, resource_id: int | None) -> None:
        if resource_id is not None and self.resource_repository.get(resource_id) is None:
            raise InvalidListeningSentenceError("Source resource not found")


def _normalize_draft(draft: ListeningSentenceDraft) -> ListeningSentenceDraft:
    sentence = " ".join(draft.sentence.split())
    if not sentence:
        raise InvalidListeningSentenceError("Sentence is required")
    return ListeningSentenceDraft(
        sentence=sentence,
        meaning=" ".join(draft.meaning.split()),
        learned_on=draft.learned_on,
        practice_status=draft.practice_status,
        note=draft.note.strip(),
        source_resource_id=draft.source_resource_id,
        source_context=draft.source_context.strip(),
        add_to_review=draft.add_to_review,
    )
