from datetime import date

from app.ai_agent.contracts import (
    AIProviderRequest,
    AgentPrincipal,
    AgentRunResult,
    AgentToolName,
)
from app.ai_agent.provider import AIProvider
from app.ai_agent.tools import AgentExecutionContext, AgentToolRegistry


DEFAULT_SYSTEM_PROMPT = """You are the planning assistant for one English learner.
Use only the provided tools for measured facts. Never invent scores, study history,
review results, or reasons. Explain recommendations in plain language and preserve
the deterministic plan as the baseline. You cannot access database tables directly."""


class LearningAgentService:
    def __init__(
        self,
        provider: AIProvider,
        tools: AgentToolRegistry,
        *,
        max_tool_rounds: int = 6,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    ) -> None:
        if max_tool_rounds < 1 or max_tool_rounds > 20:
            raise ValueError("max_tool_rounds must be between 1 and 20")
        self.provider = provider
        self.tools = tools
        self.max_tool_rounds = max_tool_rounds
        self.system_prompt = system_prompt

    def run(
        self,
        principal: AgentPrincipal,
        prompt: str,
        today: date,
    ) -> AgentRunResult:
        normalized_prompt = prompt.strip()
        if not normalized_prompt:
            raise ValueError("prompt is required")
        tool_catalogue = self.tools.catalogue(principal)
        request = AIProviderRequest(
            system_prompt=self.system_prompt,
            user_prompt=normalized_prompt,
            tools=tool_catalogue,
        )
        context = AgentExecutionContext(principal=principal, today=today)
        tools_used: list[AgentToolName] = []

        for _ in range(self.max_tool_rounds + 1):
            response = self.provider.respond(request)
            if response.tool_calls:
                if len(tools_used) + len(response.tool_calls) > self.max_tool_rounds:
                    raise AgentToolRoundLimitError(
                        "Agent exceeded the configured tool-call limit"
                    )
                results = tuple(
                    self.tools.execute(
                        context,
                        call.call_id,
                        call.name,
                        call.arguments,
                    )
                    for call in response.tool_calls
                )
                tools_used.extend(call.name for call in response.tool_calls)
                request = AIProviderRequest(
                    system_prompt=self.system_prompt,
                    user_prompt=normalized_prompt,
                    tools=tool_catalogue,
                    previous_response_id=response.response_id,
                    tool_results=results,
                )
                continue
            if response.output_text:
                return AgentRunResult(
                    provider_name=self.provider.provider_name,
                    response_id=response.response_id,
                    output_text=response.output_text,
                    tools_used=tuple(tools_used),
                )
        raise AgentToolRoundLimitError("Agent did not produce a final response")


class AgentToolRoundLimitError(RuntimeError):
    pass
