from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.ai_agent.contracts import AgentToolName


class WeeklyCoachingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    week_start: date
    provider_name: str
    output_text: str
    tools_used: tuple[AgentToolName, ...]
    created_at: datetime
