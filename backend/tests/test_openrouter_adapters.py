from types import SimpleNamespace

import pytest

from app.ai_agent.contracts import (
    AIProviderRequest,
    AgentPermission,
    AgentToolDefinition,
    AgentToolName,
    AgentToolResult,
)
from app.domain.ai_evaluation.entities import (
    EvaluationSourceType,
    WorkEvaluationRequest,
)
from app.domain.learning_evidence.entities import Skill
from app.integrations.openai.work_evaluator import (
    CriterionOutput,
    WorkEvaluationOutput,
)
from app.integrations.openrouter.responses_provider import OpenRouterChatProvider
from app.integrations.openrouter.work_evaluator import OpenRouterWorkEvaluator


FREE_MODEL = "qwen/qwen3.8-27b:free"


def test_openrouter_provider_keeps_tool_conversation_local() -> None:
    client = _FakeClient()
    provider = OpenRouterChatProvider(model=FREE_MODEL, client=client)
    tool = AgentToolDefinition(
        name=AgentToolName.GET_SKILL_PROFILE,
        description="Read profile",
        input_schema={"type": "object", "properties": {}, "additionalProperties": False},
        required_permission=AgentPermission.READ_LEARNING_DATA,
    )
    client.chat.completions.next_response = SimpleNamespace(
        id="chat-1",
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=None,
                    reasoning_details=None,
                    tool_calls=[
                        SimpleNamespace(
                            id="call-1",
                            function=SimpleNamespace(
                                name="get_skill_profile",
                                arguments="{}",
                            ),
                        )
                    ],
                )
            )
        ],
    )

    first = provider.respond(
        AIProviderRequest(
            system_prompt="Use facts only",
            user_prompt="How am I doing?",
            tools=(tool,),
        )
    )

    assert provider.provider_name == "openrouter"
    assert first.tool_calls[0].name is AgentToolName.GET_SKILL_PROFILE
    first_call = client.chat.completions.create_calls[0]
    assert first_call["model"] == FREE_MODEL
    assert first_call["parallel_tool_calls"] is False
    assert first_call["max_tokens"] == 2000
    assert first_call["tools"][0]["function"]["name"] == "get_skill_profile"

    client.chat.completions.next_response = SimpleNamespace(
        id="chat-2",
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content="Your profile is still provisional.",
                    reasoning_details=None,
                    tool_calls=[],
                )
            )
        ],
    )
    second = provider.respond(
        AIProviderRequest(
            system_prompt="Use facts only",
            user_prompt="How am I doing?",
            tools=(tool,),
            previous_response_id="chat-1",
            tool_results=(
                AgentToolResult(
                    call_id="call-1",
                    name=AgentToolName.GET_SKILL_PROFILE,
                    output={"found": False},
                ),
            ),
        )
    )

    assert second.output_text == "Your profile is still provisional."
    continuation = client.chat.completions.create_calls[1]["messages"]
    assert continuation[2]["role"] == "assistant"
    assert continuation[2]["tool_calls"][0]["id"] == "call-1"
    assert continuation[3] == {
        "role": "tool",
        "tool_call_id": "call-1",
        "content": '{"found":false}',
    }


def test_openrouter_rejects_non_free_model() -> None:
    with pytest.raises(ValueError, match=":free"):
        OpenRouterChatProvider(
            model="qwen/qwen3.8-27b",
            client=_FakeClient(),
        )


def test_openrouter_uses_only_free_fallback_after_rate_limit() -> None:
    client = _FakeClient()
    client.chat.completions.create_errors.append(_TransientRateLimitError())
    client.chat.completions.next_response = SimpleNamespace(
        id="chat-fallback",
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content="OK",
                    reasoning_details=None,
                    tool_calls=[],
                )
            )
        ],
    )
    provider = OpenRouterChatProvider(model=FREE_MODEL, client=client)

    result = provider.respond(
        AIProviderRequest(
            system_prompt="Be concise",
            user_prompt="Reply OK",
            tools=(),
        )
    )

    assert result.output_text == "OK"
    assert [item["model"] for item in client.chat.completions.create_calls] == [
        FREE_MODEL,
        "openrouter/free",
    ]


def test_openrouter_evaluator_uses_structured_chat_output() -> None:
    client = _FakeClient()
    client.chat.completions.next_parsed = WorkEvaluationOutput(
        overall_score=70,
        summary="The request is clear but needs more precise grammar.",
        criteria=[
            CriterionOutput(
                key="clarity",
                label="Clarity",
                score=3.5,
                maximum_score=5,
                explanation="The purpose is easy to identify.",
                evidence=["change my appointment"],
            )
        ],
        strengths=["Clear purpose"],
        improvement_priorities=["Use articles accurately"],
        corrections=[],
        suggested_revision="I would like to change my appointment.",
    )
    evaluator = OpenRouterWorkEvaluator(model=FREE_MODEL, client=client)
    request = WorkEvaluationRequest(
        user_key="learner",
        resource_id=1,
        skill=Skill.WRITING,
        source_type=EvaluationSourceType.WRITING_SUBMISSION,
        source_id=5,
        source_revision=1,
        task_prompt="Write a request letter.",
        learner_text="I want change my appointment.",
        supporting_context="formal letter",
        input_fingerprint="a" * 64,
    )

    result = evaluator.evaluate(request)

    assert result.provider_name == "openrouter"
    assert result.model_name == FREE_MODEL
    assert result.evaluator_version.startswith("openrouter-english-work-v1:")
    parse_call = client.chat.completions.parse_calls[0]
    assert parse_call["response_format"] is WorkEvaluationOutput
    assert parse_call["max_tokens"] == 2000


class _FakeCompletions:
    def __init__(self) -> None:
        self.create_calls: list[dict] = []
        self.parse_calls: list[dict] = []
        self.create_errors: list[Exception] = []
        self.next_response = None
        self.next_parsed = None

    def create(self, **kwargs):
        self.create_calls.append(kwargs)
        if self.create_errors:
            raise self.create_errors.pop(0)
        return self.next_response

    def parse(self, **kwargs):
        self.parse_calls.append(kwargs)
        return SimpleNamespace(
            model=kwargs["model"],
            choices=[SimpleNamespace(message=SimpleNamespace(parsed=self.next_parsed))],
        )


class _FakeChat:
    def __init__(self) -> None:
        self.completions = _FakeCompletions()


class _FakeClient:
    def __init__(self) -> None:
        self.chat = _FakeChat()


class _TransientRateLimitError(RuntimeError):
    status_code = 429
