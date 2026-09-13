from dataclasses import dataclass


@dataclass(frozen=True)
class WeaknessDetectionConfig:
    # Change this whenever classification semantics change.
    detector_version: str = "rule-based-v1"
    recent_snapshot_limit: int = 4
    minimum_scored_snapshots: int = 2
    confirmation_window: int = 2
    weak_score_below: float = 55.0
    developing_score_below: float = 70.0
    strong_score_at_least: float = 85.0
    score_precision: int = 1


DEFAULT_WEAKNESS_DETECTION_CONFIG = WeaknessDetectionConfig()
