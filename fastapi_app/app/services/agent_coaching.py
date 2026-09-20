import logging
from collections.abc import Callable
from datetime import date, timedelta

from app.ai_agent.contracts import (
    AgentPermission,
    AgentPrincipal,
    AgentToolName,
)
from app.ai_agent.service import LearningAgentService
from app.domain.agent_coaching.entities import (
    WeeklyCoachingDraft,
    WeeklyCoachingReport,
)
from app.domain.agent_coaching.repository import AgentCoachingRepository


LOGGER = logging.getLogger(__name__)


WEEKLY_COACHING_PROMPT = """请生成本周英语学习教练报告。
必须先调用 generate_weekly_report、get_skill_profile、get_weak_skills 和
get_due_reviews；只能引用这些工具返回的可测量事实。请用简洁中文输出：
1. 本周结论；2. 有数字依据的优势与弱项；3. 下周三个具体行动。
证据不足时明确写“证据不足”。不要预测官方 IELTS/PTE 分数，不要声称已经
修改计划，也不要建议超出学习系统中已有证据的内容。"""

WEEKLY_COACHING_TOOLS = frozenset(
    {
        AgentToolName.GENERATE_WEEKLY_REPORT,
        AgentToolName.GET_SKILL_PROFILE,
        AgentToolName.GET_WEAK_SKILLS,
        AgentToolName.GET_DUE_REVIEWS,
    }
)


class AgentCoachingService:
    def __init__(
        self,
        repository: AgentCoachingRepository,
        agent_factory: Callable[[], LearningAgentService | None],
        *,
        available: bool,
        unavailable_reason: str,
    ) -> None:
        self.repository = repository
        self.agent_factory = agent_factory
        self.available = available
        self.unavailable_reason = unavailable_reason

    def get_latest(
        self,
        user_key: str,
        today: date,
    ) -> WeeklyCoachingReport | None:
        return self.repository.get_latest(user_key, _week_start(today))

    def generate(
        self,
        user_key: str,
        today: date,
    ) -> WeeklyCoachingReport:
        if not self.available:
            raise AgentCoachingUnavailableError(self.unavailable_reason)
        agent = self.agent_factory()
        if agent is None:
            raise AgentCoachingUnavailableError(self.unavailable_reason)
        try:
            result = agent.run(
                AgentPrincipal(
                    user_key=user_key,
                    permissions=frozenset({AgentPermission.READ_LEARNING_DATA}),
                    allowed_tools=WEEKLY_COACHING_TOOLS,
                ),
                WEEKLY_COACHING_PROMPT,
                today,
            )
        except Exception as error:
            LOGGER.exception("AI weekly coaching generation failed")
            raise AgentCoachingGenerationError(
                "AI coaching could not be generated"
            ) from error
        missing_tools = WEEKLY_COACHING_TOOLS - set(result.tools_used)
        if missing_tools:
            missing = ", ".join(sorted(item.value for item in missing_tools))
            raise AgentCoachingGenerationError(
                f"AI coaching omitted required evidence tools: {missing}"
            )
        return self.repository.save(
            WeeklyCoachingDraft(
                user_key=user_key,
                week_start=_week_start(today),
                provider_name=result.provider_name,
                response_id=result.response_id,
                output_text=result.output_text,
                tools_used=result.tools_used,
            )
        )


class AgentCoachingUnavailableError(RuntimeError):
    pass


class AgentCoachingGenerationError(RuntimeError):
    pass


def _week_start(value: date) -> date:
    return value - timedelta(days=value.weekday())
