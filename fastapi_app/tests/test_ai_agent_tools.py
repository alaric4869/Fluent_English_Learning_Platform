from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.ai_agent.authorization import AgentToolAuthorizationError
from app.ai_agent.capabilities import (
    MockAgentCapabilityGenerator,
    RecommendationGenerationRequest,
    WeeklyNarrativeRequest,
)
from app.ai_agent.contracts import (
    AIProviderResponse,
    AgentPermission,
    AgentPrincipal,
    AgentToolName,
    ProviderToolCall,
)
from app.ai_agent.provider import MockAIProvider
from app.ai_agent.service import LearningAgentService
from app.ai_agent.tools import AgentExecutionContext, AgentToolInputError
from app.composition import build_agent_tool_registry, build_application_services
from app.database import Base
from app.domain.learning_evidence.entities import Skill
from app.models.learning_evidence import LearningResource


TODAY = date(2026, 9, 20)


def test_agent_tool_catalogue_is_typed_and_read_only_by_default() -> None:
    with _services() as (_, services):
        registry = build_agent_tool_registry(services)
        principal = AgentPrincipal(user_key="learner")

        catalogue = registry.catalogue(principal)

        assert {item.name for item in catalogue} == set(AgentToolName)
        assert all(
            item.required_permission is AgentPermission.READ_LEARNING_DATA
            for item in catalogue
        )
        search = next(
            item
            for item in catalogue
            if item.name is AgentToolName.SEARCH_LEARNING_RESOURCES
        )
        assert "user_key" not in search.input_schema.get("properties", {})
        assert search.input_schema["additionalProperties"] is False


def test_tool_context_owns_user_identity_and_rejects_injected_user_key() -> None:
    with _services() as (_, services):
        registry = build_agent_tool_registry(services)
        principal = AgentPrincipal(user_key="learner")
        context = AgentExecutionContext(principal=principal, today=TODAY)

        with pytest.raises(AgentToolInputError):
            registry.execute(
                context,
                "call-1",
                AgentToolName.GET_SKILL_PROFILE,
                {"user_key": "another-user"},
            )


def test_policy_hides_and_rejects_tools_without_permission() -> None:
    with _services() as (_, services):
        registry = build_agent_tool_registry(services)
        principal = AgentPrincipal(user_key="learner", permissions=frozenset())
        context = AgentExecutionContext(principal=principal, today=TODAY)

        assert registry.catalogue(principal) == ()
        with pytest.raises(AgentToolAuthorizationError):
            registry.execute(
                context,
                "call-1",
                AgentToolName.GET_TODAY_PLAN,
                {},
            )


def test_principal_can_be_restricted_to_a_smaller_tool_allow_list() -> None:
    with _services() as (_, services):
        registry = build_agent_tool_registry(services)
        principal = AgentPrincipal(
            user_key="learner",
            allowed_tools=frozenset({AgentToolName.GET_SKILL_PROFILE}),
        )
        context = AgentExecutionContext(principal=principal, today=TODAY)

        assert tuple(item.name for item in registry.catalogue(principal)) == (
            AgentToolName.GET_SKILL_PROFILE,
        )
        with pytest.raises(AgentToolAuthorizationError):
            registry.execute(
                context,
                "call-1",
                AgentToolName.GET_DUE_REVIEWS,
                {},
            )


def test_resource_tools_use_application_services_and_user_scope() -> None:
    with _services() as (session, services):
        session.add_all(
            [
                LearningResource(
                    slug="listening-a",
                    title="Australian appointment call",
                    resource_type="audio",
                    skill=Skill.LISTENING.value,
                    topic="Appointments",
                    difficulty="intermediate",
                    estimated_duration_minutes=18,
                    content={},
                    tags=["Australia", "phone"],
                    priority=80,
                    active=True,
                ),
                LearningResource(
                    slug="reading-a",
                    title="Rental notice",
                    resource_type="article",
                    skill=Skill.READING.value,
                    topic="Housing",
                    difficulty="intermediate",
                    estimated_duration_minutes=15,
                    content={},
                    tags=["Australia", "housing"],
                    priority=60,
                    active=True,
                ),
            ]
        )
        session.commit()
        registry = build_agent_tool_registry(services)
        context = AgentExecutionContext(
            principal=AgentPrincipal(user_key="learner"),
            today=TODAY,
        )

        search = registry.execute(
            context,
            "call-search",
            AgentToolName.SEARCH_LEARNING_RESOURCES,
            {"skill": "listening", "search": "appointment"},
        )
        recommendations = registry.execute(
            context,
            "call-recommend",
            AgentToolName.RECOMMEND_RESOURCES,
            {"skill": "listening", "count": 2},
        )

        assert search.output["total_count"] == 1
        assert search.output["items"][0]["title"] == "Australian appointment call"
        assert recommendations.output["classification"] == "insufficient_evidence"
        assert recommendations.output["items"][0]["title"] == (
            "Australian appointment call"
        )


def test_mock_provider_executes_tool_loop_without_database_access() -> None:
    with _services() as (session, services):
        session.add(
            LearningResource(
                slug="agent-resource",
                title="Natural café conversation",
                resource_type="audio",
                skill=Skill.LISTENING.value,
                topic="Ordering food",
                difficulty="intermediate",
                estimated_duration_minutes=12,
                content={},
                tags=["conversation"],
                priority=80,
                active=True,
            )
        )
        session.commit()
        provider = MockAIProvider(
            (
                AIProviderResponse(
                    response_id="response-1",
                    tool_calls=(
                        ProviderToolCall(
                            call_id="call-1",
                            name=AgentToolName.SEARCH_LEARNING_RESOURCES,
                            arguments={"skill": "listening", "limit": 5},
                        ),
                    ),
                ),
                AIProviderResponse(
                    response_id="response-2",
                    output_text="今天可以练习自然咖啡店对话。",
                ),
            )
        )
        agent = LearningAgentService(provider, build_agent_tool_registry(services))

        result = agent.run(
            AgentPrincipal(user_key="learner"),
            "推荐今天的听力材料",
            TODAY,
        )

        assert result.output_text == "今天可以练习自然咖啡店对话。"
        assert result.tools_used == (
            AgentToolName.SEARCH_LEARNING_RESOURCES,
        )
        assert provider.requests[1].previous_response_id == "response-1"
        tool_result = provider.requests[1].tool_results[0]
        assert tool_result.output["items"][0]["title"] == "Natural café conversation"


def test_mock_capability_interfaces_preserve_measured_reasons() -> None:
    generator = MockAgentCapabilityGenerator()

    recommendation = generator.generate_recommendation(
        RecommendationGenerationRequest(
            objective="Improve listening retention",
            measured_reasons=("Three recent sessions averaged 58% accuracy.",),
        )
    )
    report = generator.generate_weekly_narrative(
        WeeklyNarrativeRequest(
            measured_summary="Four study days completed.",
            measured_highlights=("Listening needs more practice.",),
        )
    )

    assert recommendation.provider_name == "mock"
    assert recommendation.reasons == (
        "Three recent sessions averaged 58% accuracy.",
    )
    assert report.summary == "Four study days completed."


class _ServicesContext:
    def __init__(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine, expire_on_commit=False)
        self.services = build_application_services(self.session)

    def __enter__(self):
        return self.session, self.services

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.session.close()
        self.engine.dispose()


def _services() -> _ServicesContext:
    return _ServicesContext()
