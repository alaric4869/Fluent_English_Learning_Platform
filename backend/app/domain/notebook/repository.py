from typing import Protocol

from app.domain.notebook.entities import NoteDraft, NotebookNote, NoteType


class NotebookRepository(Protocol):
    def create(self, user_key: str, draft: NoteDraft) -> NotebookNote: ...

    def list_notes(
        self,
        user_key: str,
        search: str,
        note_type: NoteType | None,
        limit: int,
    ) -> tuple[NotebookNote, ...]: ...
