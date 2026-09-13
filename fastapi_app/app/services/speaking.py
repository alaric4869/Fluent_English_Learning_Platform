from app.domain.resources.repository import ResourceRepository
from app.domain.speaking.entities import RetellingDraft, RetellingRecord
from app.domain.speaking.repository import SpeakingPracticeRepository


class InvalidRetellingError(ValueError):
    pass


class SpeakingPracticeService:
    def __init__(
        self,
        repository: SpeakingPracticeRepository,
        resource_repository: ResourceRepository,
    ) -> None:
        self.repository = repository
        self.resource_repository = resource_repository

    def save_retelling(self, user_key: str, draft: RetellingDraft) -> RetellingRecord:
        normalized = _normalize_draft(draft)
        if normalized.source_resource_id is not None and self.resource_repository.get(
            normalized.source_resource_id
        ) is None:
            raise InvalidRetellingError("Source resource not found")
        return self.repository.create(user_key, normalized)

    def list_retellings(
        self,
        user_key: str,
        search: str = "",
        limit: int = 200,
    ) -> tuple[RetellingRecord, ...]:
        if limit < 1 or limit > 500:
            raise ValueError("limit must be between 1 and 500")
        return self.repository.list_records(user_key, search.strip(), limit)


def _normalize_draft(draft: RetellingDraft) -> RetellingDraft:
    prompt = " ".join(draft.prompt.split())
    if not prompt:
        raise InvalidRetellingError("Retelling prompt is required")
    vocabulary = tuple(
        value for value in dict.fromkeys(" ".join(item.split()) for item in draft.intended_vocabulary) if value
    )
    return RetellingDraft(
        prompt=prompt,
        written_outline=draft.written_outline.strip(),
        intended_vocabulary=vocabulary,
        mistakes=draft.mistakes.strip(),
        improved_version=draft.improved_version.strip(),
        practice_status=draft.practice_status,
        source_resource_id=draft.source_resource_id,
        source_context=draft.source_context.strip(),
        voice_recording_reference=draft.voice_recording_reference,
    )
