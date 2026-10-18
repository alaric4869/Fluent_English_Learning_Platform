from datetime import datetime

from pydantic import BaseModel


class EvaluationCriterionResponse(BaseModel):
    key: str
    label: str
    score: float
    maximum_score: float
    explanation: str
    evidence: list[str]


class EvaluationCorrectionResponse(BaseModel):
    original: str
    suggested: str
    reason: str


class WorkEvaluationResponse(BaseModel):
    id: int
    source_revision: int
    provider_name: str
    model_name: str
    overall_score: float
    summary: str
    criteria: list[EvaluationCriterionResponse]
    strengths: list[str]
    improvement_priorities: list[str]
    corrections: list[EvaluationCorrectionResponse]
    suggested_revision: str
    created_at: datetime
    created: bool
