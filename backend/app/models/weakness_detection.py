from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class WeaknessAssessmentRunModel(Base):
    __tablename__ = "weakness_assessment_runs"
    __table_args__ = (
        UniqueConstraint("learner_profile_id", "detector_version", "evidence_fingerprint"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    learner_profile_id: Mapped[int] = mapped_column(
        ForeignKey("learner_profiles.id"),
        index=True,
    )
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    detector_version: Mapped[str] = mapped_column(String(60))
    evidence_fingerprint: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    skills: Mapped[list["WeaknessSkillAssessmentModel"]] = relationship(
        back_populates="assessment_run",
        cascade="all, delete-orphan",
    )


class WeaknessSkillAssessmentModel(Base):
    __tablename__ = "weakness_skill_assessments"
    __table_args__ = (UniqueConstraint("assessment_run_id", "skill"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_run_id: Mapped[int] = mapped_column(
        ForeignKey("weakness_assessment_runs.id"),
        index=True,
    )
    skill: Mapped[str] = mapped_column(String(30), index=True)
    classification: Mapped[str] = mapped_column(String(40), index=True)
    smoothed_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    latest_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    scored_snapshot_count: Mapped[int] = mapped_column(Integer)
    latest_average_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    latest_average_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    latest_hard_item_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    latest_accuracy_trend: Mapped[float | None] = mapped_column(Float, nullable=True)
    evidence_snapshot_ids: Mapped[list[int]] = mapped_column(JSON)
    reasons: Mapped[list[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    assessment_run: Mapped[WeaknessAssessmentRunModel] = relationship(back_populates="skills")
