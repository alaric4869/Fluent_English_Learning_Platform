from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.domain.speaking.entities import (
    RetellingDraft,
    RetellingDraftStatus,
    RetellingRecord,
    RetellingSubmission,
    RetellingWorkspaceInput,
    ShadowingSentenceProgress,
    SpeakingPracticeStatus,
)
from app.models.practice_notes import RetellingRecordModel
from app.models.speaking import (
    SpeakingRetellingSubmissionModel,
    SpeakingSentenceProgressModel,
)


class SqlAlchemySpeakingPracticeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, user_key: str, draft: RetellingDraft) -> RetellingRecord:
        item = RetellingRecordModel(
            user_key=user_key,
            prompt=draft.prompt,
            written_outline=draft.written_outline,
            intended_vocabulary=list(draft.intended_vocabulary),
            retelling_text=draft.retelling_text,
            mistakes=draft.mistakes,
            improved_version=draft.improved_version,
            practice_status=draft.practice_status.value,
            source_resource_id=draft.source_resource_id,
            source_context=draft.source_context,
            voice_recording_reference=draft.voice_recording_reference,
            workspace_managed=draft.workspace_managed,
            active_duration_seconds=draft.active_duration_seconds,
            perceived_difficulty=draft.perceived_difficulty,
            confidence=draft.confidence,
        )
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return to_retelling_record(item)

    def list_records(
        self,
        user_key: str,
        search: str,
        limit: int,
    ) -> tuple[RetellingRecord, ...]:
        statement = select(RetellingRecordModel).where(
            RetellingRecordModel.user_key == user_key
        )
        if search:
            pattern = f"%{search.casefold()}%"
            statement = statement.where(
                or_(
                    func.lower(RetellingRecordModel.prompt).like(pattern),
                    func.lower(RetellingRecordModel.written_outline).like(pattern),
                    func.lower(RetellingRecordModel.retelling_text).like(pattern),
                    func.lower(RetellingRecordModel.mistakes).like(pattern),
                    func.lower(RetellingRecordModel.improved_version).like(pattern),
                    func.lower(RetellingRecordModel.source_context).like(pattern),
                )
            )
        statement = statement.order_by(
            RetellingRecordModel.created_at.desc(), RetellingRecordModel.id.desc()
        ).limit(limit)
        return tuple(to_retelling_record(item) for item in self.session.scalars(statement))

    def get_workspace_record(
        self,
        user_key: str,
        resource_id: int,
    ) -> RetellingRecord | None:
        row = self._get_workspace_row(user_key, resource_id)
        return to_retelling_record(row) if row is not None else None

    def save_workspace_record(
        self,
        user_key: str,
        resource_id: int,
        prompt: str,
        source_context: str,
        draft_input: RetellingWorkspaceInput,
        occurred_at: datetime,
    ) -> RetellingRecord:
        row = self._get_workspace_row(user_key, resource_id)
        if row is None:
            row = RetellingRecordModel(
                user_key=user_key,
                source_resource_id=resource_id,
                workspace_managed=True,
                started_at=occurred_at,
                created_at=occurred_at,
            )
            self.session.add(row)
        changed_after_submission = row.status == RetellingDraftStatus.SUBMITTED.value and (
            row.written_outline != draft_input.written_outline
            or row.intended_vocabulary != list(draft_input.intended_vocabulary)
            or row.retelling_text != draft_input.retelling_text
            or row.mistakes != draft_input.mistakes
            or row.improved_version != draft_input.improved_version
            or row.practice_status != draft_input.practice_status.value
            or row.perceived_difficulty != draft_input.perceived_difficulty
            or row.confidence != draft_input.confidence
        )
        row.prompt = prompt
        row.source_context = source_context
        row.written_outline = draft_input.written_outline
        row.intended_vocabulary = list(draft_input.intended_vocabulary)
        row.retelling_text = draft_input.retelling_text
        row.mistakes = draft_input.mistakes
        row.improved_version = draft_input.improved_version
        row.practice_status = draft_input.practice_status.value
        row.active_duration_seconds = max(
            row.active_duration_seconds or 0,
            draft_input.active_duration_seconds,
        )
        row.perceived_difficulty = draft_input.perceived_difficulty
        row.confidence = draft_input.confidence
        if changed_after_submission:
            row.status = RetellingDraftStatus.IN_PROGRESS.value
            row.submitted_at = None
        row.updated_at = occurred_at
        self.session.commit()
        self.session.refresh(row)
        return to_retelling_record(row)

    def submit_workspace_record(
        self,
        user_key: str,
        resource_id: int,
        occurred_at: datetime,
    ) -> tuple[RetellingRecord, RetellingSubmission]:
        row = self._get_workspace_row(user_key, resource_id)
        if row is None:
            raise LookupError("Speaking draft not found")
        if row.status == RetellingDraftStatus.SUBMITTED.value:
            existing = self.session.scalar(
                select(SpeakingRetellingSubmissionModel).where(
                    SpeakingRetellingSubmissionModel.retelling_record_id == row.id,
                    SpeakingRetellingSubmissionModel.revision == row.submission_revision,
                )
            )
            if existing is None:
                raise RuntimeError("Submitted speaking draft has no submission snapshot")
            return to_retelling_record(row), _to_submission(existing, created=False)

        revision = row.submission_revision + 1
        previously_recorded_seconds = self.session.scalar(
            select(
                func.coalesce(
                    func.sum(SpeakingRetellingSubmissionModel.active_duration_seconds),
                    0,
                )
            ).where(SpeakingRetellingSubmissionModel.retelling_record_id == row.id)
        ) or 0
        submission = SpeakingRetellingSubmissionModel(
            retelling_record_id=row.id,
            revision=revision,
            written_outline_snapshot=row.written_outline,
            intended_vocabulary_snapshot=list(row.intended_vocabulary),
            retelling_text_snapshot=row.retelling_text,
            mistakes_snapshot=row.mistakes,
            improved_version_snapshot=row.improved_version,
            practice_status=row.practice_status,
            active_duration_seconds=max(
                0,
                row.active_duration_seconds - previously_recorded_seconds,
            ),
            perceived_difficulty=row.perceived_difficulty,
            confidence=row.confidence,
            submitted_at=occurred_at,
            created_at=occurred_at,
        )
        row.status = RetellingDraftStatus.SUBMITTED.value
        row.submission_revision = revision
        row.submitted_at = occurred_at
        row.updated_at = occurred_at
        self.session.add(submission)
        self.session.commit()
        self.session.refresh(row)
        self.session.refresh(submission)
        return to_retelling_record(row), _to_submission(submission, created=True)

    def list_sentence_progress(
        self,
        user_key: str,
        resource_id: int,
    ) -> tuple[ShadowingSentenceProgress, ...]:
        statement = (
            select(SpeakingSentenceProgressModel)
            .where(
                SpeakingSentenceProgressModel.user_key == user_key,
                SpeakingSentenceProgressModel.resource_id == resource_id,
            )
            .order_by(SpeakingSentenceProgressModel.id)
        )
        return tuple(_to_sentence_progress(row) for row in self.session.scalars(statement))

    def save_sentence_progress(
        self,
        user_key: str,
        resource_id: int,
        sentence_key: str,
        practice_status: SpeakingPracticeStatus,
        occurred_at: datetime,
    ) -> ShadowingSentenceProgress:
        row = self.session.scalar(
            select(SpeakingSentenceProgressModel).where(
                SpeakingSentenceProgressModel.user_key == user_key,
                SpeakingSentenceProgressModel.resource_id == resource_id,
                SpeakingSentenceProgressModel.sentence_key == sentence_key,
            )
        )
        if row is None:
            row = SpeakingSentenceProgressModel(
                user_key=user_key,
                resource_id=resource_id,
                sentence_key=sentence_key,
                practice_status=practice_status.value,
                practice_count=1,
                created_at=occurred_at,
                updated_at=occurred_at,
            )
            self.session.add(row)
        else:
            row.practice_status = practice_status.value
            row.practice_count += 1
            row.updated_at = occurred_at
        self.session.commit()
        self.session.refresh(row)
        return _to_sentence_progress(row)

    def _get_workspace_row(
        self,
        user_key: str,
        resource_id: int,
    ) -> RetellingRecordModel | None:
        return self.session.scalar(
            select(RetellingRecordModel)
            .where(
                RetellingRecordModel.user_key == user_key,
                RetellingRecordModel.source_resource_id == resource_id,
                RetellingRecordModel.workspace_managed.is_(True),
            )
            .order_by(RetellingRecordModel.id.desc())
        )


def to_retelling_record(item: RetellingRecordModel) -> RetellingRecord:
    return RetellingRecord(
        id=item.id,
        user_key=item.user_key,
        prompt=item.prompt,
        written_outline=item.written_outline,
        intended_vocabulary=tuple(item.intended_vocabulary),
        retelling_text=item.retelling_text,
        mistakes=item.mistakes,
        improved_version=item.improved_version,
        practice_status=SpeakingPracticeStatus(item.practice_status),
        source_resource_id=item.source_resource_id,
        source_context=item.source_context,
        voice_recording_reference=item.voice_recording_reference,
        workspace_managed=item.workspace_managed,
        active_duration_seconds=item.active_duration_seconds,
        perceived_difficulty=item.perceived_difficulty,
        confidence=item.confidence,
        status=RetellingDraftStatus(item.status),
        submission_revision=item.submission_revision,
        started_at=_as_utc(item.started_at),
        submitted_at=_as_utc(item.submitted_at),
        created_at=_as_utc(item.created_at),
        updated_at=_as_utc(item.updated_at),
    )


def _to_submission(
    row: SpeakingRetellingSubmissionModel,
    *,
    created: bool,
) -> RetellingSubmission:
    return RetellingSubmission(
        id=row.id,
        retelling_record_id=row.retelling_record_id,
        revision=row.revision,
        written_outline_snapshot=row.written_outline_snapshot,
        intended_vocabulary_snapshot=tuple(row.intended_vocabulary_snapshot),
        retelling_text_snapshot=row.retelling_text_snapshot,
        mistakes_snapshot=row.mistakes_snapshot,
        improved_version_snapshot=row.improved_version_snapshot,
        practice_status=SpeakingPracticeStatus(row.practice_status),
        active_duration_seconds=row.active_duration_seconds,
        perceived_difficulty=row.perceived_difficulty,
        confidence=row.confidence,
        submitted_at=_as_utc(row.submitted_at),
        created=created,
    )


def _to_sentence_progress(
    row: SpeakingSentenceProgressModel,
) -> ShadowingSentenceProgress:
    return ShadowingSentenceProgress(
        id=row.id,
        user_key=row.user_key,
        resource_id=row.resource_id,
        sentence_key=row.sentence_key,
        practice_status=SpeakingPracticeStatus(row.practice_status),
        practice_count=row.practice_count,
        created_at=_as_utc(row.created_at),
        updated_at=_as_utc(row.updated_at),
    )


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
