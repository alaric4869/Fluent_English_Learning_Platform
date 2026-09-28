import json
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from app.domain.ai_evaluation.entities import (
    EvaluationCorrection,
    EvaluationCriterion,
    GeneratedWorkEvaluation,
    WorkEvaluationRequest,
)


class StructuredResponsesClient(Protocol):
    @property
    def responses(self):
        ...


class _StrictOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CriterionOutput(_StrictOutput):
    key: str
    label: str
    score: float = Field(ge=0, le=5)
    maximum_score: float = Field(default=5, gt=0, le=5)
    explanation: str
    evidence: list[str]


class CorrectionOutput(_StrictOutput):
    original: str
    suggested: str
    reason: str


class WorkEvaluationOutput(_StrictOutput):
    overall_score: float = Field(ge=0, le=100)
    summary: str
    criteria: list[CriterionOutput]
    strengths: list[str]
    improvement_priorities: list[str]
    corrections: list[CorrectionOutput]
    suggested_revision: str


class OpenAIWorkEvaluator:
    available = True
    provider_name = "openai"

    def __init__(
        self,
        *,
        model: str,
        api_key: str | None = None,
        max_output_tokens: int = 2000,
        client: StructuredResponsesClient | None = None,
    ) -> None:
        normalized_model = model.strip()
        if not normalized_model:
            raise ValueError("An OpenAI evaluation model must be configured")
        if not 256 <= max_output_tokens <= 8192:
            raise ValueError("max_output_tokens must be between 256 and 8192")
        if client is None:
            try:
                from openai import OpenAI
            except ImportError as error:
                raise RuntimeError(
                    "Install the optional AI dependency with: pip install -e '.[ai]'"
                ) from error
            if not api_key:
                raise RuntimeError("OPENAI_API_KEY is required for AI evaluation")
            client = OpenAI(api_key=api_key)
        self.model_name = normalized_model
        self.max_output_tokens = max_output_tokens
        self.client = client
        self.evaluator_version = (
            f"{self.provider_name}-english-work-v1:{self.model_name}"
        )

    def evaluate(self, request: WorkEvaluationRequest) -> GeneratedWorkEvaluation:
        response = self.client.responses.parse(
            model=self.model_name,
            instructions=evaluation_instructions(request),
            input=json.dumps(
                {
                    "task_prompt": request.task_prompt,
                    "learner_text": request.learner_text,
                    "supporting_context": request.supporting_context,
                },
                ensure_ascii=False,
            ),
            text_format=WorkEvaluationOutput,
            max_output_tokens=self.max_output_tokens,
            store=False,
        )
        parsed = response.output_parsed
        if parsed is None:
            raise InvalidStructuredEvaluationError(
                "OpenAI returned no structured evaluation"
            )
        return self.build_result(parsed)

    def build_result(
        self,
        parsed: WorkEvaluationOutput,
        *,
        model_name: str | None = None,
    ) -> GeneratedWorkEvaluation:
        return GeneratedWorkEvaluation(
            provider_name=self.provider_name,
            model_name=model_name or self.model_name,
            evaluator_version=self.evaluator_version,
            overall_score=parsed.overall_score,
            summary=parsed.summary,
            criteria=tuple(
                EvaluationCriterion(
                    key=item.key,
                    label=item.label,
                    score=item.score,
                    maximum_score=item.maximum_score,
                    explanation=item.explanation,
                    evidence=tuple(item.evidence),
                )
                for item in parsed.criteria
            ),
            strengths=tuple(parsed.strengths),
            improvement_priorities=tuple(parsed.improvement_priorities),
            corrections=tuple(
                EvaluationCorrection(
                    original=item.original,
                    suggested=item.suggested,
                    reason=item.reason,
                )
                for item in parsed.corrections
            ),
            suggested_revision=parsed.suggested_revision,
        )


def evaluation_instructions(request: WorkEvaluationRequest) -> str:
    if request.skill.value == "writing":
        criteria = (
            "task fulfilment, coherence and cohesion, lexical resource, "
            "and grammatical range and accuracy"
        )
    else:
        criteria = (
            "clarity, organization, vocabulary use, grammatical control, "
            "and natural spoken-style phrasing"
        )
    return (
        "Evaluate this English learner's submitted text using these criteria: "
        f"{criteria}. Give actionable feedback grounded only in the supplied text. "
        "Use a 0-100 coaching score, not an official IELTS/PTE Band score. "
        "Never claim to assess pronunciation, accent, or audio fluency from text. "
        "Keep quoted evidence short and preserve the learner's original meaning."
    )


class InvalidStructuredEvaluationError(RuntimeError):
    pass
