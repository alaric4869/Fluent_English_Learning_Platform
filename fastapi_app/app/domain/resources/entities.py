from dataclasses import dataclass
from datetime import date, datetime

from app.domain.learning_evidence.entities import Skill


@dataclass(frozen=True)
class ResourceCandidate:
    id: int
    slug: str
    title: str
    resource_type: str
    skill: Skill
    topic: str
    difficulty: str | None
    estimated_duration_minutes: int
    priority: int
    tags: tuple[str, ...]
    last_studied_at: datetime | None
    last_assigned_date: date | None
    completed_session_count: int


@dataclass(frozen=True)
class ResourceRecommendation:
    resource_id: int
    score: float
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class LearningResourceDetails:
    id: int
    slug: str
    title: str
    resource_type: str
    skill: Skill
    topic: str
    difficulty: str | None
    estimated_duration_minutes: int
    priority: int
    tags: tuple[str, ...]
    active: bool
