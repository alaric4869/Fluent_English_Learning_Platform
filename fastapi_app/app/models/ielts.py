from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PracticeSet(Base):
    __tablename__ = "ielts_practice_sets"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    book_number: Mapped[int] = mapped_column(Integer)
    test_number: Mapped[int] = mapped_column(Integer)
    skill: Mapped[str] = mapped_column(String(30), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    duration_minutes: Mapped[int] = mapped_column(Integer)
    content_version: Mapped[str] = mapped_column(String(40))
    sections: Mapped[list["PracticeSection"]] = relationship(
        back_populates="practice_set", cascade="all, delete-orphan", order_by="PracticeSection.order_index"
    )
    attempts: Mapped[list["PracticeAttempt"]] = relationship(
        back_populates="practice_set", cascade="all, delete-orphan"
    )


class PracticeSection(Base):
    __tablename__ = "ielts_practice_sections"
    __table_args__ = (UniqueConstraint("practice_set_id", "order_index"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    practice_set_id: Mapped[int] = mapped_column(ForeignKey("ielts_practice_sets.id"), index=True)
    order_index: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(160))
    instructions: Mapped[str] = mapped_column(Text)
    content_blocks: Mapped[list[dict]] = mapped_column(JSON, default=list)
    audio_path: Mapped[str | None] = mapped_column(String(300), nullable=True)
    practice_set: Mapped[PracticeSet] = relationship(back_populates="sections")
    questions: Mapped[list["PracticeQuestion"]] = relationship(
        back_populates="section", cascade="all, delete-orphan", order_by="PracticeQuestion.number"
    )


class PracticeQuestion(Base):
    __tablename__ = "ielts_practice_questions"
    __table_args__ = (UniqueConstraint("practice_set_id", "number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    practice_set_id: Mapped[int] = mapped_column(ForeignKey("ielts_practice_sets.id"), index=True)
    section_id: Mapped[int] = mapped_column(ForeignKey("ielts_practice_sections.id"), index=True)
    number: Mapped[int] = mapped_column(Integer)
    prompt: Mapped[str] = mapped_column(Text)
    question_type: Mapped[str] = mapped_column(String(40))
    options: Mapped[list[dict]] = mapped_column(JSON, default=list)
    accepted_answers: Mapped[list[str]] = mapped_column(JSON)
    answer_group: Mapped[str | None] = mapped_column(String(80), nullable=True)
    explanation: Mapped[str] = mapped_column(Text)
    section: Mapped[PracticeSection] = relationship(back_populates="questions")


class PracticeAttempt(Base):
    __tablename__ = "ielts_practice_attempts"
    __table_args__ = (UniqueConstraint("practice_set_id", "user_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    practice_set_id: Mapped[int] = mapped_column(ForeignKey("ielts_practice_sets.id"), index=True)
    user_key: Mapped[str] = mapped_column(String(120), index=True)
    status: Mapped[str] = mapped_column(String(20), default="in_progress")
    answers: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    results: Mapped[list[dict]] = mapped_column(JSON, default=list)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    practice_set: Mapped[PracticeSet] = relationship(back_populates="attempts")

