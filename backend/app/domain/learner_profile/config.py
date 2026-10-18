from dataclasses import dataclass


@dataclass(frozen=True)
class LearnerProfileConfig:
    # Change this whenever scoring semantics change so old snapshots remain auditable.
    algorithm_version: str = "rule-based-v2-subjective"
    recent_session_limit: int = 5
    minimum_established_samples: int = 2
    minimum_trend_samples: int = 4
    accuracy_weight: float = 0.75
    confidence_weight: float = 0.15
    hard_item_weight: float = 0.10
    subjective_confidence_weight: float = 0.60
    subjective_difficulty_weight: float = 0.40
    score_precision: int = 1


DEFAULT_LEARNER_PROFILE_CONFIG = LearnerProfileConfig()
