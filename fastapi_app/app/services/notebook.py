from app.domain.notebook.entities import NoteDraft, NotebookNote, NoteType
from app.domain.notebook.repository import NotebookRepository
from app.domain.resources.repository import ResourceRepository


class InvalidNoteError(ValueError):
    pass


class NotebookService:
    def __init__(
        self,
        repository: NotebookRepository,
        resource_repository: ResourceRepository,
    ) -> None:
        self.repository = repository
        self.resource_repository = resource_repository

    def add_note(self, user_key: str, draft: NoteDraft) -> NotebookNote:
        normalized = _normalize_draft(draft)
        if normalized.source_resource_id is not None and self.resource_repository.get(
            normalized.source_resource_id
        ) is None:
            raise InvalidNoteError("Source resource not found")
        return self.repository.create(user_key, normalized)

    def get_notes(
        self,
        user_key: str,
        search: str = "",
        note_type: NoteType | None = None,
        limit: int = 200,
    ) -> tuple[NotebookNote, ...]:
        if limit < 1 or limit > 500:
            raise ValueError("limit must be between 1 and 500")
        return self.repository.list_notes(user_key, search.strip(), note_type, limit)


def _normalize_draft(draft: NoteDraft) -> NoteDraft:
    title = " ".join(draft.title.split())
    content = draft.content.strip()
    if not title:
        raise InvalidNoteError("Note title is required")
    if not content:
        raise InvalidNoteError("Note content is required")
    tags = tuple(
        value for value in dict.fromkeys(" ".join(item.split()) for item in draft.tags) if value
    )
    return NoteDraft(
        note_type=draft.note_type,
        title=title,
        content=content,
        source_resource_id=draft.source_resource_id,
        source_context=draft.source_context.strip(),
        tags=tags,
    )
