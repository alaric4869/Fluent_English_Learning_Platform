from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum

from app.domain.learning_evidence.entities import Skill
from app.domain.resources.entities import ResourceRecommendation
from app.domain.weakness_detection.entities import SkillClassification


class StudyPlanStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"


class StudyPlanItemStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass(frozen=True)
class SkillPlanningSignal:
    skill: Skill
    classification: SkillClassification
    assessment_reasons: tuple[str, ...]
    resource_recommendation: ResourceRecommendation | None


@dataclass(frozen=True)
class StudyPlanGenerationContext:
    user_key: str
    plan_date: date
    weakness_assessment_run_id: int | None
    recommender_version: str
    skill_signals: tuple[SkillPlanningSignal, ...]


@dataclass(frozen=True)
class StudyPlanItemProposal:
    skill: Skill
    position: int
    planned_minutes: int
    resource_id: int | None
    recommendation_score: float | None
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class StudyPlanProposal:
    user_key: str
    plan_date: date
    source: str
    generator_version: str
    weakness_assessment_run_id: int | None
    recommender_version: str
    total_minutes: int
    explanation: tuple[str, ...]
    items: tuple[StudyPlanItemProposal, ...]


@dataclass(frozen=True)
class DailyStudyPlanItem:
    id: int
    skill: Skill
    position: int
    system_planned_minutes: int
    planned_minutes: int
    system_resource_id: int | None
    resource_id: int | None
    status: StudyPlanItemStatus
    recommendation_score: float | None
    reasons: tuple[str, ...]
    manual_override: bool
    override_note: str
    started_at: datetime | None
    completed_at: datetime | None


@dataclass(frozen=True)
class DailyStudyPlan:
    id: int
    user_key: str
    plan_date: date
    status: StudyPlanStatus
    source: str
    generator_version: str
    weakness_assessment_run_id: int | None
    recommender_version: str
    total_minutes: int
    explanation: tuple[str, ...]
    items: tuple[DailyStudyPlanItem, ...]
    created_at: datetime
    updated_at: datetime
    created: bool
