from app.domain.ai_evaluation.entities import (
    EvaluationCriterion,
    GeneratedWorkEvaluation,
    WorkEvaluationRequest,
)


class MockWorkEvaluator:
    """Deterministic evaluator for tests; its output is visibly non-production."""

    evaluator_version = "mock-evaluator-v1"
    available = True

    def evaluate(self, request: WorkEvaluationRequest) -> GeneratedWorkEvaluation:
        return GeneratedWorkEvaluation(
            provider_name="mock",
            model_name="mock",
            evaluator_version=self.evaluator_version,
            overall_score=60.0,
            summary="Mock evaluation for offline verification only.",
            criteria=(
                EvaluationCriterion(
                    key="clarity",
                    label="Clarity",
                    score=3.0,
                    maximum_score=5.0,
                    explanation="The response communicates its main idea.",
                    evidence=(request.learner_text[:120],),
                ),
            ),
            strengths=("A main idea is present.",),
            improvement_priorities=("Add more specific supporting detail.",),
            corrections=(),
            suggested_revision=request.learner_text,
        )


class UnavailableWorkEvaluator:
    evaluator_version = "unavailable"
    available = False

    def evaluate(self, request: WorkEvaluationRequest) -> GeneratedWorkEvaluation:
        raise WorkEvaluatorUnavailableError(
            "AI evaluation is not configured. Set the provider, model and API key."
        )


class WorkEvaluatorUnavailableError(RuntimeError):
    pass
