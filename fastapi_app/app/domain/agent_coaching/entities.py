from dataclasses import dataclass
from datetime import date, datetime

from app.ai_agent.contracts import AgentToolName


@dataclass(frozen=True, slots=True)
class WeeklyCoachingDraft:
    user_key: str
    week_start: date
    provider_name: str
    response_id: str
    output_text: str
    tools_used: tuple[AgentToolName, ...]


@dataclass(frozen=True, slots=True)
class WeeklyCoachingReport:
    id: int
    draft: WeeklyCoachingDraft
    created_at: datetime
