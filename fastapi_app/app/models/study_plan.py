from datetime import date, datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StudyPlanModel(Base):
    __tablename__ = "study_plans"
    __table_args__ = (UniqueConstraint("user_key", "plan_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_key: Mapped[str] = mapped_column(String(120), index=True)
    plan_date: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(30), index=True)
    source: Mapped[str] = mapped_column(String(40))
    generator_version: Mapped[str] = mapped_column(String(60))
    weakness_assessment_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("weakness_assessment_runs.id"),
        nullable=True,
        index=True,
    )
    recommender_version: Mapped[str] = mapped_column(String(60))
    total_minutes: Mapped[int] = mapped_column(Integer)
    explanation: Mapped[list[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
    items: Mapped[list["StudyPlanItemModel"]] = relationship(
        back_populates="study_plan",
        cascade="all, delete-orphan",
        order_by="StudyPlanItemModel.position",
    )


class StudyPlanItemModel(Base):
    __tablename__ = "study_plan_items"
    __table_args__ = (
        UniqueConstraint("study_plan_id", "skill"),
        UniqueConstraint("study_plan_id", "position"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    study_plan_id: Mapped[int] = mapped_column(ForeignKey("study_plans.id"), index=True)
    skill: Mapped[str] = mapped_column(String(30), index=True)
    position: Mapped[int] = mapped_column(Integer)
    system_planned_minutes: Mapped[int] = mapped_column(Integer)
    planned_minutes: Mapped[int] = mapped_column(Integer)
    system_resource_id: Mapped[int | None] = mapped_column(
        ForeignKey("learning_resources.id"),
        nullable=True,
    )
    resource_id: Mapped[int | None] = mapped_column(
        ForeignKey("learning_resources.id"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(30), index=True)
    recommendation_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    reasons: Mapped[list[str]] = mapped_column(JSON)
    manual_override: Mapped[bool] = mapped_column(Boolean, default=False)
    override_note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
    study_plan: Mapped[StudyPlanModel] = relationship(back_populates="items")
