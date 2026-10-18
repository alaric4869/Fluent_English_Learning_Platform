from datetime import date, datetime, timezone

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SavedSentenceModel(Base):
    __tablename__ = "saved_sentences"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_key: Mapped[str] = mapped_column(String(120), index=True)
    sentence: Mapped[str] = mapped_column(Text)
    meaning: Mapped[str] = mapped_column(Text, default="")
    learned_on: Mapped[date] = mapped_column(Date, index=True)
    practice_status: Mapped[str] = mapped_column(String(40), index=True)
    note: Mapped[str] = mapped_column(Text, default="")
    source_resource_id: Mapped[int | None] = mapped_column(
        ForeignKey("learning_resources.id"), nullable=True, index=True
    )
    source_context: Mapped[str] = mapped_column(Text, default="")
    favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    saved_for_later: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    review_item: Mapped["ReviewItemModel | None"] = relationship(
        back_populates="saved_sentence",
        cascade="all, delete-orphan",
        uselist=False,
    )


class RetellingRecordModel(Base):
    __tablename__ = "speaking_retelling_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_key: Mapped[str] = mapped_column(String(120), index=True)
    prompt: Mapped[str] = mapped_column(Text)
    written_outline: Mapped[str] = mapped_column(Text, default="")
    intended_vocabulary: Mapped[list[str]] = mapped_column(JSON, default=list)
    retelling_text: Mapped[str] = mapped_column(Text, default="")
    mistakes: Mapped[str] = mapped_column(Text, default="")
    improved_version: Mapped[str] = mapped_column(Text, default="")
    practice_status: Mapped[str] = mapped_column(String(40), index=True)
    source_resource_id: Mapped[int | None] = mapped_column(
        ForeignKey("learning_resources.id"), nullable=True, index=True
    )
    source_context: Mapped[str] = mapped_column(Text, default="")
    voice_recording_reference: Mapped[str | None] = mapped_column(
        String(1000), nullable=True
    )
    workspace_managed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    active_duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    perceived_difficulty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="in_progress", index=True)
    submission_revision: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    submissions: Mapped[list["SpeakingRetellingSubmissionModel"]] = relationship(
        back_populates="retelling_record",
        cascade="all, delete-orphan",
    )


class NotebookNoteModel(Base):
    __tablename__ = "notebook_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_key: Mapped[str] = mapped_column(String(120), index=True)
    note_type: Mapped[str] = mapped_column(String(40), index=True)
    title: Mapped[str] = mapped_column(String(300))
    content: Mapped[str] = mapped_column(Text)
    source_resource_id: Mapped[int | None] = mapped_column(
        ForeignKey("learning_resources.id"), nullable=True, index=True
    )
    source_context: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    saved_for_later: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
