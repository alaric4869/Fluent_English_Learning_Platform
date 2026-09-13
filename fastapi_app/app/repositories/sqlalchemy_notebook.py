from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.domain.notebook.entities import NoteDraft, NotebookNote, NoteType
from app.models.practice_notes import NotebookNoteModel


class SqlAlchemyNotebookRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, user_key: str, draft: NoteDraft) -> NotebookNote:
        item = NotebookNoteModel(
            user_key=user_key,
            note_type=draft.note_type.value,
            title=draft.title,
            content=draft.content,
            source_resource_id=draft.source_resource_id,
            source_context=draft.source_context,
            tags=list(draft.tags),
            favorite=False,
            saved_for_later=False,
        )
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return to_notebook_note(item)

    def list_notes(
        self,
        user_key: str,
        search: str,
        note_type: NoteType | None,
        limit: int,
    ) -> tuple[NotebookNote, ...]:
        statement = select(NotebookNoteModel).where(
            NotebookNoteModel.user_key == user_key
        )
        if search:
            pattern = f"%{search.casefold()}%"
            statement = statement.where(
                or_(
                    func.lower(NotebookNoteModel.title).like(pattern),
                    func.lower(NotebookNoteModel.content).like(pattern),
                    func.lower(NotebookNoteModel.source_context).like(pattern),
                )
            )
        if note_type is not None:
            statement = statement.where(NotebookNoteModel.note_type == note_type.value)
        statement = statement.order_by(
            NotebookNoteModel.created_at.desc(), NotebookNoteModel.id.desc()
        ).limit(limit)
        return tuple(to_notebook_note(item) for item in self.session.scalars(statement))


def to_notebook_note(item: NotebookNoteModel) -> NotebookNote:
    return NotebookNote(
        id=item.id,
        user_key=item.user_key,
        note_type=NoteType(item.note_type),
        title=item.title,
        content=item.content,
        source_resource_id=item.source_resource_id,
        source_context=item.source_context,
        tags=tuple(item.tags),
        favorite=item.favorite,
        saved_for_later=item.saved_for_later,
        created_at=_as_utc(item.created_at),
        updated_at=_as_utc(item.updated_at),
    )


def _as_utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
