from datetime import date, datetime, timezone

from sqlalchemy import JSON, Date, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class WeeklyCoachingReportModel(Base):
    __tablename__ = "weekly_coaching_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_key: Mapped[str] = mapped_column(String(120), index=True)
    week_start: Mapped[date] = mapped_column(Date, index=True)
    provider_name: Mapped[str] = mapped_column(String(60), index=True)
    response_id: Mapped[str] = mapped_column(String(200))
    output_text: Mapped[str] = mapped_column(Text)
    tools_used: Mapped[list[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        index=True,
    )
