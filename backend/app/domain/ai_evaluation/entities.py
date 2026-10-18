from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.learning_evidence.entities import Skill


class EvaluationSourceType(StrEnum):
    WRITING_SUBMISSION = "writing_submission"
    RETELLING_SUBMISSION = "retelling_submission"


@dataclass(frozen=True)
class WorkEvaluationRequest:
    user_key: str
    resource_id: int
    skill: Skill
    source_type: EvaluationSourceType
    source_id: int
    source_revision: int
    task_prompt: str
    learner_text: str
    supporting_context: str
    input_fingerprint: str


@dataclass(frozen=True)
class EvaluationCriterion:
    key: str
    label: str
    score: float
    maximum_score: float
    explanation: str
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class EvaluationCorrection:
    original: str
    suggested: str
    reason: str


@dataclass(frozen=True)
class GeneratedWorkEvaluation:
    provider_name: str
    model_name: str
    evaluator_version: str
    overall_score: float
    summary: str
    criteria: tuple[EvaluationCriterion, ...]
    strengths: tuple[str, ...]
    improvement_priorities: tuple[str, ...]
    corrections: tuple[EvaluationCorrection, ...]
    suggested_revision: str


@dataclass(frozen=True)
class StoredWorkEvaluation:
    id: int
    request: WorkEvaluationRequest
    result: GeneratedWorkEvaluation
    created_at: datetime
    created: bool
