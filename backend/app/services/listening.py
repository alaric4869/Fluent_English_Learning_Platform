from datetime import date

from app.domain.listening.entities import (
    ListeningSentenceDraft,
    ListeningSentenceStatus,
    SavedListeningSentence,
)
from app.domain.listening.repository import ListeningSentenceRepository
from app.domain.listening.transcript import split_transcript
from app.domain.learning_evidence.entities import Skill
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

    def list_for_resource(
        self,
        user_key: str,
        resource_id: int,
    ) -> tuple[SavedListeningSentence, ...]:
        self._get_listening_resource(user_key, resource_id)
        return self.repository.list_for_resource(user_key, resource_id)

    def mark_transcript_sentence(
        self,
        user_key: str,
        resource_id: int,
        sentence: str,
        status: ListeningSentenceStatus,
        today: date,
    ) -> SavedListeningSentence:
        resource = self._get_listening_resource(user_key, resource_id)
        normalized_sentence = " ".join(sentence.split())
        if not normalized_sentence:
            raise InvalidListeningSentenceError("Sentence is required")
        if normalized_sentence not in split_transcript(resource.transcript):
            raise InvalidListeningSentenceError(
                "Sentence does not belong to this resource transcript"
            )
        existing = self.repository.find_for_resource_sentence(
            user_key, resource_id, normalized_sentence
        )
        should_review = status in {
            ListeningSentenceStatus.COULD_NOT_HEAR,
            ListeningSentenceStatus.DIFFICULT,
        }
        schedule = self.review_scheduler.initial_state(today) if should_review else None
        if existing is not None:
            updated = self.repository.update_status(
                user_key,
                existing.id,
                status,
                schedule,
            )
            if updated is None:
                raise LookupError("Saved sentence not found")
            return updated
        return self.repository.create(
            user_key,
            ListeningSentenceDraft(
                sentence=normalized_sentence,
                meaning="",
                learned_on=today,
                practice_status=status,
                source_resource_id=resource_id,
                source_context=resource.title,
                add_to_review=should_review,
            ),
            schedule,
        )

    def _validate_resource(self, resource_id: int | None) -> None:
        if resource_id is not None and self.resource_repository.get(resource_id) is None:
            raise InvalidListeningSentenceError("Source resource not found")

    def _get_listening_resource(self, user_key: str, resource_id: int):
        resource = self.resource_repository.get_for_user(user_key, resource_id)
        if resource is None:
            raise LookupError("Listening resource not found")
        if resource.skill is not Skill.LISTENING:
            raise InvalidListeningSentenceError("Resource is not a listening resource")
        return resource


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
