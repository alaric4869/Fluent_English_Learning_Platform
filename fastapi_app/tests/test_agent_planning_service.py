from datetime import date

import pytest

from app.ai_agent.contracts import AgentRunResult, AgentToolName
from app.services.agent_planning import (
    PLAN_RECOMMENDATION_ALLOWED_TOOLS,
    PLAN_RECOMMENDATION_REQUIRED_TOOLS,
    AgentPlanningService,
    AgentPlanningUnavailableError,
)


TODAY = date(2026, 9, 22)


class FakeAdaptationDecisions:
    def get_pending_ai_recommendations(self, user_key, plan_date):
        assert user_key == "learner"
        assert plan_date == TODAY
        return (object(),)


class FakeAgent:
    def __init__(self) -> None:
        self.principal = None

    def run(self, principal, prompt, today):
        self.principal = principal
        assert today == TODAY
        assert "save_ai_recommendation" in prompt
        return AgentRunResult(
            provider_name="test-provider",
            response_id="response-1",
            output_text="已保存一条待确认建议。",
            tools_used=tuple(PLAN_RECOMMENDATION_REQUIRED_TOOLS),
        )


def test_agent_planning_uses_a_bounded_allow_list_and_returns_pending_count() -> None:
    agent = FakeAgent()
    service = AgentPlanningService(
        FakeAdaptationDecisions(),
        lambda: agent,
        available=True,
        unavailable_reason="",
    )

    result = service.generate_recommendations("learner", TODAY)

    assert result.pending_count == 1
    assert agent.principal.allowed_tools == PLAN_RECOMMENDATION_ALLOWED_TOOLS
    assert {item.value for item in agent.principal.permissions} == {
        "read_learning_data",
        "save_ai_recommendation",
    }


def test_disabled_agent_planning_never_builds_a_provider() -> None:
    service = AgentPlanningService(
        FakeAdaptationDecisions(),
        lambda: pytest.fail("provider factory must not be called"),
        available=False,
        unavailable_reason="AI disabled",
    )

    with pytest.raises(AgentPlanningUnavailableError, match="AI disabled"):
        service.generate_recommendations("learner", TODAY)
