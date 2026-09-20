from datetime import date
from typing import Protocol

from app.domain.agent_coaching.entities import (
    WeeklyCoachingDraft,
    WeeklyCoachingReport,
)


class AgentCoachingRepository(Protocol):
    def get_latest(
        self,
        user_key: str,
        week_start: date,
    ) -> WeeklyCoachingReport | None: ...

    def save(self, draft: WeeklyCoachingDraft) -> WeeklyCoachingReport: ...
