from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class LearnerProfile(Base):
    __tablename__ = "learner_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_key: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
    snapshots: Mapped[list["LearnerProfileSnapshotModel"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
    )


class LearnerProfileSnapshotModel(Base):
    __tablename__ = "learner_profile_snapshots"
    __table_args__ = (
        UniqueConstraint("learner_profile_id", "algorithm_version", "evidence_fingerprint"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    learner_profile_id: Mapped[int] = mapped_column(
        ForeignKey("learner_profiles.id"),
        index=True,
    )
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    algorithm_version: Mapped[str] = mapped_column(String(60))
    evidence_fingerprint: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    profile: Mapped[LearnerProfile] = relationship(back_populates="snapshots")
    skills: Mapped[list["LearnerSkillSnapshot"]] = relationship(
        back_populates="profile_snapshot",
        cascade="all, delete-orphan",
    )


class LearnerSkillSnapshot(Base):
    __tablename__ = "learner_skill_snapshots"
    __table_args__ = (UniqueConstraint("profile_snapshot_id", "skill"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("learner_profile_snapshots.id"),
        index=True,
    )
    skill: Mapped[str] = mapped_column(String(30), index=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    evidence_status: Mapped[str] = mapped_column(String(30))
    sample_count: Mapped[int] = mapped_column(Integer)
    average_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    average_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    average_difficulty: Mapped[float | None] = mapped_column(Float, nullable=True)
    hard_item_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    accuracy_trend: Mapped[float | None] = mapped_column(Float, nullable=True)
    evidence_ids: Mapped[list[int]] = mapped_column(JSON)
    calculation_weights: Mapped[dict[str, float]] = mapped_column(JSON)
    explanation: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    profile_snapshot: Mapped[LearnerProfileSnapshotModel] = relationship(back_populates="skills")
