from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class WritingDraftModel(Base):
    __tablename__ = "writing_drafts"
    __table_args__ = (UniqueConstraint("user_key", "resource_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_key: Mapped[str] = mapped_column(String(120), index=True)
    resource_id: Mapped[int] = mapped_column(
        ForeignKey("learning_resources.id"), index=True
    )
    response_text: Mapped[str] = mapped_column(Text, default="")
    outline: Mapped[str] = mapped_column(Text, default="")
    word_count: Mapped[int] = mapped_column(Integer, default=0)
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
    submissions: Mapped[list["WritingSubmissionModel"]] = relationship(
        back_populates="draft",
        cascade="all, delete-orphan",
    )


class WritingSubmissionModel(Base):
    __tablename__ = "writing_submissions"
    __table_args__ = (UniqueConstraint("writing_draft_id", "revision"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    writing_draft_id: Mapped[int] = mapped_column(
        ForeignKey("writing_drafts.id"), index=True
    )
    revision: Mapped[int] = mapped_column(Integer)
    response_snapshot: Mapped[str] = mapped_column(Text)
    outline_snapshot: Mapped[str] = mapped_column(Text, default="")
    word_count: Mapped[int] = mapped_column(Integer)
    active_duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    perceived_difficulty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    draft: Mapped[WritingDraftModel] = relationship(back_populates="submissions")
