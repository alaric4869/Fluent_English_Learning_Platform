import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from app.ai_agent.contracts import (
    AgentPermission,
    AgentPrincipal,
    AgentToolName,
)
from app.ai_agent.service import LearningAgentService
from app.services.adaptive_learning import AdaptationDecisionService


LOGGER = logging.getLogger(__name__)

PLAN_RECOMMENDATION_PROMPT = """请检查今天已经存在的学习计划，并给出谨慎的小幅调整建议。
你必须先调用 get_today_plan、get_skill_profile、get_weak_skills 和 get_due_reviews。
只有结构化证据支持修改时，才调用 save_ai_recommendation；最多保存两个建议。
如要替换材料，必须先调用 recommend_resources，并只能使用其返回的材料 ID。
每个保存的建议必须包含具体数字依据。不得直接修改计划，不得覆盖用户选择，不得预测
IELTS/PTE 官方分数。最后用简洁中文说明保存了什么；证据不足时明确说明未保存建议。"""

PLAN_RECOMMENDATION_REQUIRED_TOOLS = frozenset(
    {
        AgentToolName.GET_TODAY_PLAN,
        AgentToolName.GET_SKILL_PROFILE,
        AgentToolName.GET_WEAK_SKILLS,
        AgentToolName.GET_DUE_REVIEWS,
    }
)
PLAN_RECOMMENDATION_ALLOWED_TOOLS = frozenset(
    {
        *PLAN_RECOMMENDATION_REQUIRED_TOOLS,
        AgentToolName.RECOMMEND_RESOURCES,
        AgentToolName.SAVE_AI_RECOMMENDATION,
    }
)


@dataclass(frozen=True)
class AgentPlanRecommendationResult:
    output_text: str
    tools_used: tuple[AgentToolName, ...]
    pending_count: int


class AgentPlanningService:
    def __init__(
        self,
        adaptation_decisions: AdaptationDecisionService,
        agent_factory: Callable[[], LearningAgentService | None],
        *,
        available: bool,
        unavailable_reason: str,
    ) -> None:
        self.adaptation_decisions = adaptation_decisions
        self.agent_factory = agent_factory
        self.available = available
        self.unavailable_reason = unavailable_reason

    def generate_recommendations(
        self,
        user_key: str,
        today: date,
    ) -> AgentPlanRecommendationResult:
        if not self.available:
            raise AgentPlanningUnavailableError(self.unavailable_reason)
        agent = self.agent_factory()
        if agent is None:
            raise AgentPlanningUnavailableError(self.unavailable_reason)
        try:
            result = agent.run(
                AgentPrincipal(
                    user_key=user_key,
                    permissions=frozenset(
                        {
                            AgentPermission.READ_LEARNING_DATA,
                            AgentPermission.SAVE_AI_RECOMMENDATION,
                        }
                    ),
                    allowed_tools=PLAN_RECOMMENDATION_ALLOWED_TOOLS,
                ),
                PLAN_RECOMMENDATION_PROMPT,
                today,
            )
        except Exception as error:
            LOGGER.exception("AI plan recommendation generation failed")
            raise AgentPlanningGenerationError(
                "AI plan recommendations could not be generated"
            ) from error
        missing_tools = PLAN_RECOMMENDATION_REQUIRED_TOOLS - set(result.tools_used)
        if missing_tools:
            missing = ", ".join(sorted(item.value for item in missing_tools))
            raise AgentPlanningGenerationError(
                f"AI planning omitted required evidence tools: {missing}"
            )
        pending = self.adaptation_decisions.get_pending_ai_recommendations(
            user_key, today
        )
        return AgentPlanRecommendationResult(
            output_text=result.output_text,
            tools_used=result.tools_used,
            pending_count=len(pending),
        )


class AgentPlanningUnavailableError(RuntimeError):
    pass


class AgentPlanningGenerationError(RuntimeError):
    pass
