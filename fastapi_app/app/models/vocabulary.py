from datetime import date, datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class VocabularyItemModel(Base):
    __tablename__ = "vocabulary_items"
    __table_args__ = (UniqueConstraint("user_key", "normalized_chunk"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_key: Mapped[str] = mapped_column(String(120), index=True)
    chunk: Mapped[str] = mapped_column(String(300))
    normalized_chunk: Mapped[str] = mapped_column(String(300))
    meaning: Mapped[str] = mapped_column(Text)
    example_sentence: Mapped[str] = mapped_column(Text, default="")
    learned_on: Mapped[date] = mapped_column(Date, index=True)
    personal_note: Mapped[str] = mapped_column(Text, default="")
    difficulty: Mapped[str] = mapped_column(String(30), index=True)
    mastery_status: Mapped[str] = mapped_column(String(30), index=True)
    source_resource_id: Mapped[int | None] = mapped_column(
        ForeignKey("learning_resources.id"),
        nullable=True,
        index=True,
    )
    source_context: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    saved_for_later: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
    review_item: Mapped["ReviewItemModel"] = relationship(
        back_populates="vocabulary_item",
        cascade="all, delete-orphan",
        uselist=False,
    )


class ReviewItemModel(Base):
    __tablename__ = "review_items"
    __table_args__ = (
        Index("ix_review_items_user_key_next_review_date", "user_key", "next_review_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_key: Mapped[str] = mapped_column(String(120), index=True)
    item_type: Mapped[str] = mapped_column(String(40), index=True)
    vocabulary_item_id: Mapped[int] = mapped_column(
        ForeignKey("vocabulary_items.id"),
        unique=True,
    )
    scheduler_version: Mapped[str] = mapped_column(String(60))
    schedule_step: Mapped[int] = mapped_column(Integer)
    next_review_date: Mapped[date] = mapped_column(Date, index=True)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
    vocabulary_item: Mapped[VocabularyItemModel] = relationship(
        back_populates="review_item"
    )
    attempts: Mapped[list["ReviewAttemptModel"]] = relationship(
        back_populates="review_item",
        cascade="all, delete-orphan",
    )


class ReviewAttemptModel(Base):
    __tablename__ = "review_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    review_item_id: Mapped[int] = mapped_column(
        ForeignKey("review_items.id"),
        index=True,
    )
    request_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    rating: Mapped[str] = mapped_column(String(20), index=True)
    previous_step: Mapped[int] = mapped_column(Integer)
    next_step: Mapped[int] = mapped_column(Integer)
    previous_review_date: Mapped[date] = mapped_column(Date)
    next_review_date: Mapped[date] = mapped_column(Date)
    interval_days: Mapped[int] = mapped_column(Integer)
    previous_mastery_status: Mapped[str] = mapped_column(String(30))
    new_mastery_status: Mapped[str] = mapped_column(String(30))
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    review_item: Mapped[ReviewItemModel] = relationship(back_populates="attempts")
