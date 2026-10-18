from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SpeakingSentenceProgressModel(Base):
    __tablename__ = "speaking_sentence_progress"
    __table_args__ = (UniqueConstraint("user_key", "resource_id", "sentence_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_key: Mapped[str] = mapped_column(String(120), index=True)
    resource_id: Mapped[int] = mapped_column(
        ForeignKey("learning_resources.id"), index=True
    )
    sentence_key: Mapped[str] = mapped_column(String(120))
    practice_status: Mapped[str] = mapped_column(String(40), index=True)
    practice_count: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class SpeakingRetellingSubmissionModel(Base):
    __tablename__ = "speaking_retelling_submissions"
    __table_args__ = (UniqueConstraint("retelling_record_id", "revision"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    retelling_record_id: Mapped[int] = mapped_column(
        ForeignKey("speaking_retelling_records.id"), index=True
    )
    revision: Mapped[int] = mapped_column(Integer)
    written_outline_snapshot: Mapped[str] = mapped_column(Text, default="")
    intended_vocabulary_snapshot: Mapped[list[str]] = mapped_column(JSON, default=list)
    retelling_text_snapshot: Mapped[str] = mapped_column(Text, default="")
    mistakes_snapshot: Mapped[str] = mapped_column(Text, default="")
    improved_version_snapshot: Mapped[str] = mapped_column(Text, default="")
    practice_status: Mapped[str] = mapped_column(String(40))
    active_duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    perceived_difficulty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    retelling_record: Mapped["RetellingRecordModel"] = relationship(
        back_populates="submissions"
    )
