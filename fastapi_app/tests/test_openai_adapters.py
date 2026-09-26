from types import SimpleNamespace

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
from app.integrations.openai.responses_provider import OpenAIResponsesProvider
from app.integrations.openai.work_evaluator import (
    CriterionOutput,
    OpenAIWorkEvaluator,
    WorkEvaluationOutput,
)


def test_openai_provider_maps_typed_tools_and_function_outputs() -> None:
    client = _FakeClient()
    provider = OpenAIResponsesProvider(model="configured-model", client=client)
    tool = AgentToolDefinition(
        name=AgentToolName.GET_SKILL_PROFILE,
        description="Read profile",
        input_schema={"type": "object", "properties": {}, "additionalProperties": False},
        required_permission=AgentPermission.READ_LEARNING_DATA,
    )
    client.responses.next_response = SimpleNamespace(
        id="resp-1",
        output_text="",
        output=[
            SimpleNamespace(
                type="function_call",
                call_id="call-1",
                name="get_skill_profile",
                arguments="{}",
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

    assert first.tool_calls[0].name is AgentToolName.GET_SKILL_PROFILE
    assert client.responses.calls[0]["store"] is False
    assert client.responses.calls[0]["parallel_tool_calls"] is False
    assert client.responses.calls[0]["max_output_tokens"] == 2000
    assert client.responses.calls[0]["tools"][0]["name"] == "get_skill_profile"

    client.responses.next_response = SimpleNamespace(
        id="resp-2",
        output_text="Your profile is still provisional.",
        output=[],
    )
    second = provider.respond(
        AIProviderRequest(
            system_prompt="Use facts only",
            user_prompt="How am I doing?",
            tools=(tool,),
            previous_response_id="resp-1",
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
    continuation = client.responses.calls[1]
    assert continuation["previous_response_id"] == "resp-1"
    assert continuation["input"][0]["type"] == "function_call_output"
    assert continuation["input"][0]["output"] == '{"found":false}'


def test_openai_evaluator_uses_structured_output_without_official_band() -> None:
    client = _FakeClient()
    client.responses.next_parsed = WorkEvaluationOutput(
        overall_score=72,
        summary="Clear purpose with some repetitive wording.",
        criteria=[
            CriterionOutput(
                key="clarity",
                label="Clarity",
                score=3.5,
                maximum_score=5,
                explanation="The main request is easy to identify.",
                evidence=["I am writing to request"],
            )
        ],
        strengths=["Clear purpose"],
        improvement_priorities=["Vary sentence openings"],
        corrections=[],
        suggested_revision="I am writing to request a change to my appointment.",
    )
    evaluator = OpenAIWorkEvaluator(model="configured-model", client=client)
    request = WorkEvaluationRequest(
        user_key="learner",
        resource_id=1,
        skill=Skill.WRITING,
        source_type=EvaluationSourceType.WRITING_SUBMISSION,
        source_id=5,
        source_revision=1,
        task_prompt="Write a request letter.",
        learner_text="I am writing to request change appointment.",
        supporting_context="formal letter",
        input_fingerprint="a" * 64,
    )

    result = evaluator.evaluate(request)

    assert result.overall_score == 72
    assert result.provider_name == "openai"
    assert result.model_name == "configured-model"
    parse_call = client.responses.parse_calls[0]
    assert parse_call["store"] is False
    assert parse_call["max_output_tokens"] == 2000
    assert "not an official IELTS/PTE Band score" in parse_call["instructions"]


class _FakeResponses:
    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.parse_calls: list[dict] = []
        self.next_response = None
        self.next_parsed = None

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.next_response

    def parse(self, **kwargs):
        self.parse_calls.append(kwargs)
        return SimpleNamespace(output_parsed=self.next_parsed)


class _FakeClient:
    def __init__(self) -> None:
        self.responses = _FakeResponses()
