from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.ai_agent.contracts import AgentRunResult, AgentToolName
from app.database import Base
from app.repositories.sqlalchemy_agent_coaching import (
    SqlAlchemyAgentCoachingRepository,
)
from app.services.agent_coaching import (
    AgentCoachingService,
    AgentCoachingUnavailableError,
    WEEKLY_COACHING_TOOLS,
)


TODAY = date(2026, 9, 20)


class FakeAgent:
    def __init__(self) -> None:
        self.principal = None

    def run(self, principal, prompt, today):
        self.principal = principal
        assert "generate_weekly_report" in prompt
        assert today == TODAY
        return AgentRunResult(
            provider_name="mock",
            response_id="response-weekly-1",
            output_text="本周完成了 3 天学习。下周优先完成到期复习。",
            tools_used=(
                AgentToolName.GENERATE_WEEKLY_REPORT,
                AgentToolName.GET_SKILL_PROFILE,
                AgentToolName.GET_WEAK_SKILLS,
                AgentToolName.GET_DUE_REVIEWS,
            ),
        )


def test_weekly_coaching_is_read_only_and_persists_latest_report() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        agent = FakeAgent()
        service = AgentCoachingService(
            SqlAlchemyAgentCoachingRepository(session),
            lambda: agent,
            available=True,
            unavailable_reason="",
        )

        report = service.generate("learner", TODAY)
        latest = service.get_latest("learner", TODAY)

        assert report.draft.week_start == date(2026, 9, 14)
        assert latest is not None
        assert latest.draft.output_text == report.draft.output_text
        assert agent.principal.allowed_tools == WEEKLY_COACHING_TOOLS
        assert {item.value for item in agent.principal.permissions} == {
            "read_learning_data"
        }
    engine.dispose()


def test_disabled_agent_never_calls_provider() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        service = AgentCoachingService(
            SqlAlchemyAgentCoachingRepository(session),
            lambda: pytest.fail("provider must not be created"),
            available=False,
            unavailable_reason="AI is disabled",
        )

        with pytest.raises(AgentCoachingUnavailableError, match="disabled"):
            service.generate("learner", TODAY)
    engine.dispose()
