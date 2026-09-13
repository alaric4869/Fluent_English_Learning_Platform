from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.domain.speaking.entities import RetellingDraft, RetellingRecord, SpeakingPracticeStatus
from app.models.practice_notes import RetellingRecordModel


class SqlAlchemySpeakingPracticeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, user_key: str, draft: RetellingDraft) -> RetellingRecord:
        item = RetellingRecordModel(
            user_key=user_key,
            prompt=draft.prompt,
            written_outline=draft.written_outline,
            intended_vocabulary=list(draft.intended_vocabulary),
            mistakes=draft.mistakes,
            improved_version=draft.improved_version,
            practice_status=draft.practice_status.value,
            source_resource_id=draft.source_resource_id,
            source_context=draft.source_context,
            voice_recording_reference=draft.voice_recording_reference,
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
                    func.lower(RetellingRecordModel.mistakes).like(pattern),
                    func.lower(RetellingRecordModel.improved_version).like(pattern),
                    func.lower(RetellingRecordModel.source_context).like(pattern),
                )
            )
        statement = statement.order_by(
            RetellingRecordModel.created_at.desc(), RetellingRecordModel.id.desc()
        ).limit(limit)
        return tuple(to_retelling_record(item) for item in self.session.scalars(statement))


def to_retelling_record(item: RetellingRecordModel) -> RetellingRecord:
    return RetellingRecord(
        id=item.id,
        user_key=item.user_key,
        prompt=item.prompt,
        written_outline=item.written_outline,
        intended_vocabulary=tuple(item.intended_vocabulary),
        mistakes=item.mistakes,
        improved_version=item.improved_version,
        practice_status=SpeakingPracticeStatus(item.practice_status),
        source_resource_id=item.source_resource_id,
        source_context=item.source_context,
        voice_recording_reference=item.voice_recording_reference,
        created_at=_as_utc(item.created_at),
        updated_at=_as_utc(item.updated_at),
    )


def _as_utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
