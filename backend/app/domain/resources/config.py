from dataclasses import dataclass

from app.domain.weakness_detection.entities import SkillClassification


@dataclass(frozen=True)
class ResourceRecommendationConfig:
    recommender_version: str = "rule-based-v1"
    unused_bonus: float = 30.0
    studied_within_7_days_penalty: float = 40.0
    studied_within_30_days_penalty: float = 15.0
    assigned_previous_day_penalty: float = 35.0
    assigned_within_7_days_penalty: float = 20.0
    exact_difficulty_bonus: float = 15.0
    difficulty_distance_penalty: float = 5.0


DIFFICULTY_RANKS = {
    "beginner": 1,
    "elementary": 1,
    "lower-intermediate": 2,
    "intermediate": 3,
    "upper-intermediate": 4,
    "advanced": 5,
}

TARGET_DIFFICULTY_RANKS = {
    SkillClassification.INSUFFICIENT_EVIDENCE: 3,
    SkillClassification.WEAK: 2,
    SkillClassification.DEVELOPING: 3,
    SkillClassification.STABLE: 3,
    SkillClassification.STRONG: 4,
}

DEFAULT_RESOURCE_RECOMMENDATION_CONFIG = ResourceRecommendationConfig()
