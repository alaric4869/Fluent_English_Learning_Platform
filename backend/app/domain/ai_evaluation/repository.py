from typing import Protocol

from app.domain.ai_evaluation.entities import (
    GeneratedWorkEvaluation,
    StoredWorkEvaluation,
    WorkEvaluationRequest,
)


class WorkEvaluationRepository(Protocol):
    def get_existing(
        self,
        request: WorkEvaluationRequest,
        evaluator_version: str,
    ) -> StoredWorkEvaluation | None:
        ...

    def get_latest_for_source(
        self,
        user_key: str,
        source_type: str,
        source_id: int,
    ) -> StoredWorkEvaluation | None:
        ...

    def save(
        self,
        request: WorkEvaluationRequest,
        result: GeneratedWorkEvaluation,
    ) -> StoredWorkEvaluation:
        ...
