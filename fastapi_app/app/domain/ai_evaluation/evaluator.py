from typing import Protocol

from app.domain.ai_evaluation.entities import (
    GeneratedWorkEvaluation,
    WorkEvaluationRequest,
)


class WorkEvaluator(Protocol):
    @property
    def evaluator_version(self) -> str:
        ...

    @property
    def available(self) -> bool:
        ...

    def evaluate(self, request: WorkEvaluationRequest) -> GeneratedWorkEvaluation:
        ...
