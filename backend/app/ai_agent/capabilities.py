from typing import Protocol

from pydantic import Field

from app.ai_agent.contracts import StrictContract


class RecommendationGenerationRequest(StrictContract):
    objective: str = Field(min_length=1, max_length=500)
    measured_reasons: tuple[str, ...]


class GeneratedRecommendation(StrictContract):
    summary: str
    reasons: tuple[str, ...]
    proposed_actions: tuple[str, ...]
    provider_name: str


class WeeklyNarrativeRequest(StrictContract):
    measured_summary: str = Field(min_length=1, max_length=2_000)
    measured_highlights: tuple[str, ...]


class GeneratedWeeklyNarrative(StrictContract):
    summary: str
    highlights: tuple[str, ...]
    next_steps: tuple[str, ...]
    provider_name: str


class AgentRecommendationGenerator(Protocol):
    def generate_recommendation(
        self,
        request: RecommendationGenerationRequest,
    ) -> GeneratedRecommendation:
        ...


class AgentReportGenerator(Protocol):
    def generate_weekly_narrative(
        self,
        request: WeeklyNarrativeRequest,
    ) -> GeneratedWeeklyNarrative:
        ...


class MockAgentCapabilityGenerator:
    """Offline seam for M16; network-backed generation is added in M17."""

    provider_name = "mock"

    def generate_recommendation(
        self,
        request: RecommendationGenerationRequest,
    ) -> GeneratedRecommendation:
        return GeneratedRecommendation(
            summary=f"Mock recommendation for: {request.objective}",
            reasons=request.measured_reasons,
            proposed_actions=("Keep the deterministic plan as the baseline.",),
            provider_name=self.provider_name,
        )

    def generate_weekly_narrative(
        self,
        request: WeeklyNarrativeRequest,
    ) -> GeneratedWeeklyNarrative:
        return GeneratedWeeklyNarrative(
            summary=request.measured_summary,
            highlights=request.measured_highlights,
            next_steps=("Use measured evidence to plan the next study week.",),
            provider_name=self.provider_name,
        )
