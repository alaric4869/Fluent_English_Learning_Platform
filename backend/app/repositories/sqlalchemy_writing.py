from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.writing.entities import (
    WritingDraft,
    WritingDraftInput,
    WritingDraftStatus,
    WritingSubmission,
)
from app.models.writing import WritingDraftModel, WritingSubmissionModel


class SqlAlchemyWritingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_draft(self, user_key: str, resource_id: int) -> WritingDraft | None:
        row = self._get_row(user_key, resource_id)
        return _to_draft(row) if row is not None else None

    def save_draft(
        self,
        user_key: str,
        resource_id: int,
        draft_input: WritingDraftInput,
        word_count: int,
        occurred_at: datetime,
    ) -> WritingDraft:
        row = self._get_row(user_key, resource_id)
        if row is None:
            row = WritingDraftModel(
                user_key=user_key,
                resource_id=resource_id,
                started_at=occurred_at,
                created_at=occurred_at,
            )
            self.session.add(row)
        changed_after_submission = row.status == WritingDraftStatus.SUBMITTED.value and (
            row.response_text != draft_input.response_text
            or row.outline != draft_input.outline
            or row.perceived_difficulty != draft_input.perceived_difficulty
            or row.confidence != draft_input.confidence
        )
        row.response_text = draft_input.response_text
        row.outline = draft_input.outline
        row.word_count = word_count
        row.active_duration_seconds = max(
            row.active_duration_seconds or 0,
            draft_input.active_duration_seconds,
        )
        row.perceived_difficulty = draft_input.perceived_difficulty
        row.confidence = draft_input.confidence
        if changed_after_submission:
            row.status = WritingDraftStatus.IN_PROGRESS.value
            row.submitted_at = None
        row.updated_at = occurred_at
        self.session.commit()
        self.session.refresh(row)
        return _to_draft(row)

    def submit(
        self,
        user_key: str,
        resource_id: int,
        occurred_at: datetime,
    ) -> tuple[WritingDraft, WritingSubmission]:
        row = self._get_row(user_key, resource_id)
        if row is None:
            raise LookupError("Writing draft not found")
        if row.status == WritingDraftStatus.SUBMITTED.value:
            existing = self.session.scalar(
                select(WritingSubmissionModel).where(
                    WritingSubmissionModel.writing_draft_id == row.id,
                    WritingSubmissionModel.revision == row.submission_revision,
                )
            )
            if existing is None:
                raise RuntimeError("Submitted writing draft has no submission snapshot")
            return _to_draft(row), _to_submission(existing, created=False)

        revision = row.submission_revision + 1
        previously_recorded_seconds = self.session.scalar(
            select(func.coalesce(func.sum(WritingSubmissionModel.active_duration_seconds), 0))
            .where(WritingSubmissionModel.writing_draft_id == row.id)
        ) or 0
        submission = WritingSubmissionModel(
            writing_draft_id=row.id,
            revision=revision,
            response_snapshot=row.response_text,
            outline_snapshot=row.outline,
            word_count=row.word_count,
            active_duration_seconds=max(
                0,
                row.active_duration_seconds - previously_recorded_seconds,
            ),
            perceived_difficulty=row.perceived_difficulty,
            confidence=row.confidence,
            submitted_at=occurred_at,
            created_at=occurred_at,
        )
        row.status = WritingDraftStatus.SUBMITTED.value
        row.submission_revision = revision
        row.submitted_at = occurred_at
        row.updated_at = occurred_at
        self.session.add(submission)
        self.session.commit()
        self.session.refresh(row)
        self.session.refresh(submission)
        return _to_draft(row), _to_submission(submission, created=True)

    def get_submission(
        self,
        user_key: str,
        resource_id: int,
        revision: int | None = None,
    ) -> WritingSubmission | None:
        statement = (
            select(WritingSubmissionModel)
            .join(WritingDraftModel)
            .where(
                WritingDraftModel.user_key == user_key,
                WritingDraftModel.resource_id == resource_id,
            )
        )
        if revision is not None:
            statement = statement.where(WritingSubmissionModel.revision == revision)
        statement = statement.order_by(WritingSubmissionModel.revision.desc())
        row = self.session.scalar(statement)
        return _to_submission(row, created=False) if row is not None else None

    def _get_row(self, user_key: str, resource_id: int) -> WritingDraftModel | None:
        return self.session.scalar(
            select(WritingDraftModel).where(
                WritingDraftModel.user_key == user_key,
                WritingDraftModel.resource_id == resource_id,
            )
        )


def _to_draft(row: WritingDraftModel) -> WritingDraft:
    return WritingDraft(
        id=row.id,
        user_key=row.user_key,
        resource_id=row.resource_id,
        response_text=row.response_text,
        outline=row.outline,
        word_count=row.word_count,
        active_duration_seconds=row.active_duration_seconds,
        perceived_difficulty=row.perceived_difficulty,
        confidence=row.confidence,
        status=WritingDraftStatus(row.status),
        submission_revision=row.submission_revision,
        started_at=_as_utc(row.started_at),
        submitted_at=_as_utc(row.submitted_at),
        created_at=_as_utc(row.created_at),
        updated_at=_as_utc(row.updated_at),
    )


def _to_submission(
    row: WritingSubmissionModel,
    *,
    created: bool,
) -> WritingSubmission:
    return WritingSubmission(
        id=row.id,
        writing_draft_id=row.writing_draft_id,
        revision=row.revision,
        response_snapshot=row.response_snapshot,
        outline_snapshot=row.outline_snapshot,
        word_count=row.word_count,
        active_duration_seconds=row.active_duration_seconds,
        perceived_difficulty=row.perceived_difficulty,
        confidence=row.confidence,
        submitted_at=_as_utc(row.submitted_at),
        created=created,
    )


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
