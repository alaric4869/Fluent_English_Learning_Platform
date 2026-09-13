from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class LearningResource(Base):
    __tablename__ = "learning_resources"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(240))
    resource_type: Mapped[str] = mapped_column(String(60), index=True)
    skill: Mapped[str] = mapped_column(String(30), index=True)
    topic: Mapped[str] = mapped_column(String(120), default="")
    difficulty: Mapped[str | None] = mapped_column(String(40), nullable=True)
    estimated_duration_minutes: Mapped[int] = mapped_column(Integer)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    local_asset_reference: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content: Mapped[dict] = mapped_column(JSON, default=dict)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    priority: Mapped[int] = mapped_column(Integer, default=50)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    owner_user_key: Mapped[str | None] = mapped_column(
        String(120), nullable=True, index=True
    )
    description: Mapped[str] = mapped_column(Text, default="")
    content_text: Mapped[str] = mapped_column(Text, default="")
    transcript: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
    practice_sets: Mapped[list["PracticeSet"]] = relationship(back_populates="learning_resource")
    study_sessions: Mapped[list["StudySession"]] = relationship(back_populates="resource")
    user_states: Mapped[list["ResourceUserState"]] = relationship(
        back_populates="resource",
        cascade="all, delete-orphan",
    )


class ResourceUserState(Base):
    __tablename__ = "resource_user_states"
    __table_args__ = (UniqueConstraint("user_key", "resource_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_key: Mapped[str] = mapped_column(String(120), index=True)
    resource_id: Mapped[int] = mapped_column(
        ForeignKey("learning_resources.id"), index=True
    )
    favorite: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    saved_for_later: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    resource: Mapped[LearningResource] = relationship(back_populates="user_states")


class StudySession(Base):
    __tablename__ = "study_sessions"
    __table_args__ = (
        UniqueConstraint("user_key", "source_type", "source_id", "source_revision"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_key: Mapped[str] = mapped_column(String(120), index=True)
    resource_id: Mapped[int] = mapped_column(ForeignKey("learning_resources.id"), index=True)
    skill: Mapped[str] = mapped_column(String(30), index=True)
    source_type: Mapped[str] = mapped_column(String(60))
    source_id: Mapped[str] = mapped_column(String(120))
    source_revision: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    actual_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    perceived_difficulty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    accuracy: Mapped[float] = mapped_column(Float)
    attempt_count: Mapped[int] = mapped_column(Integer)
    hard_item_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    incorrect_item_count: Mapped[int] = mapped_column(Integer)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    resource: Mapped[LearningResource] = relationship(back_populates="study_sessions")
    exercise_attempts: Mapped[list["ExerciseAttempt"]] = relationship(
        back_populates="study_session",
        cascade="all, delete-orphan",
    )
    skill_performances: Mapped[list["SkillPerformance"]] = relationship(
        back_populates="study_session",
        cascade="all, delete-orphan",
    )


class ExerciseAttempt(Base):
    __tablename__ = "exercise_attempts"
    __table_args__ = (UniqueConstraint("study_session_id", "exercise_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    study_session_id: Mapped[int] = mapped_column(ForeignKey("study_sessions.id"), index=True)
    exercise_id: Mapped[str] = mapped_column(String(180))
    submitted_answer: Mapped[str] = mapped_column(Text)
    correct: Mapped[bool] = mapped_column(Boolean)
    score: Mapped[float] = mapped_column(Float)
    max_score: Mapped[float] = mapped_column(Float)
    attempt_number: Mapped[int] = mapped_column(Integer)
    confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prompt_snapshot: Mapped[str] = mapped_column(Text)
    correct_answers: Mapped[list[str]] = mapped_column(JSON)
    explanation_snapshot: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    study_session: Mapped[StudySession] = relationship(back_populates="exercise_attempts")


class SkillPerformance(Base):
    __tablename__ = "skill_performances"
    __table_args__ = (UniqueConstraint("study_session_id", "skill"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    study_session_id: Mapped[int] = mapped_column(ForeignKey("study_sessions.id"), index=True)
    user_key: Mapped[str] = mapped_column(String(120), index=True)
    skill: Mapped[str] = mapped_column(String(30), index=True)
    accuracy: Mapped[float] = mapped_column(Float)
    item_count: Mapped[int] = mapped_column(Integer)
    correct_item_count: Mapped[int] = mapped_column(Integer)
    incorrect_item_count: Mapped[int] = mapped_column(Integer)
    hard_item_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    perceived_difficulty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    study_session: Mapped[StudySession] = relationship(back_populates="skill_performances")
