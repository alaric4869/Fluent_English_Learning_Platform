from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.learning_evidence.entities import Skill


class EvidenceStatus(StrEnum):
    NO_DATA = "no_data"
    PROVISIONAL = "provisional"
    ESTABLISHED = "established"


@dataclass(frozen=True)
class SkillProfileEvaluation:
    skill: Skill
    score: float | None
    evidence_status: EvidenceStatus
    sample_count: int
    average_accuracy: float | None
    average_confidence: float | None
    average_difficulty: float | None
    hard_item_rate: float | None
    accuracy_trend: float | None
    evidence_ids: tuple[int, ...]
    calculation_weights: dict[str, float]
    explanation: str


@dataclass(frozen=True)
class LearnerProfileEvaluation:
    user_key: str
    calculated_at: datetime
    algorithm_version: str
    evidence_fingerprint: str
    skills: tuple[SkillProfileEvaluation, ...]


@dataclass(frozen=True)
class LearnerProfileSnapshot:
    id: int
    user_key: str
    calculated_at: datetime
    algorithm_version: str
    evidence_fingerprint: str
    skills: tuple[SkillProfileEvaluation, ...]
    created: bool


@dataclass(frozen=True)
class HistoricalSkillProfile:
    skill_snapshot_id: int
    profile_snapshot_id: int
    calculated_at: datetime
    skill: Skill
    score: float | None
    evidence_status: EvidenceStatus
    sample_count: int
    average_accuracy: float | None
    average_confidence: float | None
    average_difficulty: float | None
    hard_item_rate: float | None
    accuracy_trend: float | None
