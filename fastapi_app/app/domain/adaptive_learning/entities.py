from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.learning_evidence.entities import Skill


class AdaptationDecisionType(StrEnum):
    SYSTEM_RECOMMENDATION = "system_recommendation"
    MANUAL_OVERRIDE = "manual_override"
    AI_RECOMMENDATION = "ai_recommendation"


class AdaptationActor(StrEnum):
    RULE_BASED = "rule_based"
    USER = "user"
    AI = "ai"


@dataclass(frozen=True)
class ManualPlanItemOverride:
    study_plan_id: int
    study_plan_item_id: int
    skill: Skill
    previous_planned_minutes: int
    new_planned_minutes: int
    previous_resource_id: int | None
    new_resource_id: int | None
    updated_plan_total_minutes: int
    remains_overridden: bool
    note: str
    decided_at: datetime


@dataclass(frozen=True)
class AIPlanItemRecommendation:
    study_plan_id: int
    study_plan_item_id: int
    skill: Skill
    current_planned_minutes: int
    proposed_planned_minutes: int
    current_resource_id: int | None
    proposed_resource_id: int | None
    reasons: tuple[str, ...]
    provider_name: str
    model_name: str
    decided_at: datetime


@dataclass(frozen=True)
class AdaptationDecision:
    id: int
    study_plan_id: int
    study_plan_item_id: int
    decision_type: AdaptationDecisionType
    actor: AdaptationActor
    skill: Skill
    previous_planned_minutes: int
    new_planned_minutes: int
    previous_resource_id: int | None
    new_resource_id: int | None
    reasons: tuple[str, ...]
    created_at: datetime
