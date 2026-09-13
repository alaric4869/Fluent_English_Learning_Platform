from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.learning_evidence.entities import Skill


class SkillClassification(StrEnum):
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    WEAK = "weak"
    DEVELOPING = "developing"
    STABLE = "stable"
    STRONG = "strong"


@dataclass(frozen=True)
class SkillWeaknessAssessment:
    skill: Skill
    classification: SkillClassification
    smoothed_score: float | None
    latest_score: float | None
    scored_snapshot_count: int
    latest_average_accuracy: float | None
    latest_average_confidence: float | None
    latest_hard_item_rate: float | None
    latest_accuracy_trend: float | None
    evidence_snapshot_ids: tuple[int, ...]
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class WeaknessAssessmentEvaluation:
    user_key: str
    assessed_at: datetime
    detector_version: str
    evidence_fingerprint: str
    skills: tuple[SkillWeaknessAssessment, ...]


@dataclass(frozen=True)
class WeaknessAssessmentRun:
    id: int
    user_key: str
    assessed_at: datetime
    detector_version: str
    evidence_fingerprint: str
    skills: tuple[SkillWeaknessAssessment, ...]
    created: bool
