from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai_agent.contracts import AgentToolName
from app.domain.agent_coaching.entities import (
    WeeklyCoachingDraft,
    WeeklyCoachingReport,
)
from app.models.agent_coaching import WeeklyCoachingReportModel


class SqlAlchemyAgentCoachingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_latest(
        self,
        user_key: str,
        week_start: date,
    ) -> WeeklyCoachingReport | None:
        row = self.session.scalar(
            select(WeeklyCoachingReportModel)
            .where(
                WeeklyCoachingReportModel.user_key == user_key,
                WeeklyCoachingReportModel.week_start == week_start,
            )
            .order_by(WeeklyCoachingReportModel.id.desc())
        )
        return _to_report(row) if row else None

    def save(self, draft: WeeklyCoachingDraft) -> WeeklyCoachingReport:
        row = WeeklyCoachingReportModel(
            user_key=draft.user_key,
            week_start=draft.week_start,
            provider_name=draft.provider_name,
            response_id=draft.response_id,
            output_text=draft.output_text,
            tools_used=[item.value for item in draft.tools_used],
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return _to_report(row)


def _to_report(row: WeeklyCoachingReportModel) -> WeeklyCoachingReport:
    created_at = row.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    return WeeklyCoachingReport(
        id=row.id,
        draft=WeeklyCoachingDraft(
            user_key=row.user_key,
            week_start=row.week_start,
            provider_name=row.provider_name,
            response_id=row.response_id,
            output_text=row.output_text,
            tools_used=tuple(AgentToolName(item) for item in row.tools_used),
        ),
        created_at=created_at,
    )
