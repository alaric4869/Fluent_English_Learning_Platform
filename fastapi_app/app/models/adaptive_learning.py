from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AdaptationDecisionModel(Base):
    __tablename__ = "adaptation_decisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    study_plan_id: Mapped[int] = mapped_column(ForeignKey("study_plans.id"), index=True)
    study_plan_item_id: Mapped[int] = mapped_column(
        ForeignKey("study_plan_items.id"),
        index=True,
    )
    decision_type: Mapped[str] = mapped_column(String(40), index=True)
    actor: Mapped[str] = mapped_column(String(30), index=True)
    skill: Mapped[str] = mapped_column(String(30), index=True)
    previous_planned_minutes: Mapped[int] = mapped_column(Integer)
    new_planned_minutes: Mapped[int] = mapped_column(Integer)
    previous_resource_id: Mapped[int | None] = mapped_column(
        ForeignKey("learning_resources.id"),
        nullable=True,
    )
    new_resource_id: Mapped[int | None] = mapped_column(
        ForeignKey("learning_resources.id"),
        nullable=True,
    )
    source_decision_id: Mapped[int | None] = mapped_column(
        ForeignKey("adaptation_decisions.id"),
        nullable=True,
        unique=True,
        index=True,
    )
    reasons: Mapped[list[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
