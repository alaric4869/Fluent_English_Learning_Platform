from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class WorkEvaluationModel(Base):
    __tablename__ = "work_evaluations"
    __table_args__ = (
        UniqueConstraint(
            "user_key",
            "source_type",
            "source_id",
            "source_revision",
            "evaluator_version",
            "input_fingerprint",
            name="uq_work_evaluation_identity",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_key: Mapped[str] = mapped_column(String(120), index=True)
    resource_id: Mapped[int] = mapped_column(
        ForeignKey("learning_resources.id"), index=True
    )
    skill: Mapped[str] = mapped_column(String(30), index=True)
    source_type: Mapped[str] = mapped_column(String(40), index=True)
    source_id: Mapped[int] = mapped_column(Integer, index=True)
    source_revision: Mapped[int] = mapped_column(Integer)
    input_fingerprint: Mapped[str] = mapped_column(String(64))
    task_prompt: Mapped[str] = mapped_column(Text)
    learner_text: Mapped[str] = mapped_column(Text)
    supporting_context: Mapped[str] = mapped_column(Text, default="")
    provider_name: Mapped[str] = mapped_column(String(60), index=True)
    model_name: Mapped[str] = mapped_column(String(120))
    evaluator_version: Mapped[str] = mapped_column(String(120), index=True)
    overall_score: Mapped[float] = mapped_column(Float)
    summary: Mapped[str] = mapped_column(Text)
    criteria: Mapped[list[dict]] = mapped_column(JSON)
    strengths: Mapped[list[str]] = mapped_column(JSON)
    improvement_priorities: Mapped[list[str]] = mapped_column(JSON)
    corrections: Mapped[list[dict]] = mapped_column(JSON)
    suggested_revision: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
