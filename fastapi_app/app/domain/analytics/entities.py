from dataclasses import dataclass
from datetime import date

from app.domain.learning_evidence.entities import Skill
from app.domain.learner_profile.entities import EvidenceStatus
from app.domain.weakness_detection.entities import SkillClassification


@dataclass(frozen=True)
class DailyActivity:
    activity_date: date
    assigned_modules: int
    completed_modules: int
    completed_planned_minutes: int
    completed_sessions: int
    tracked_seconds: int


@dataclass(frozen=True)
class SkillProgressSummary:
    skill: Skill
    completed_modules: int
    completed_sessions: int
    profile_score: float | None
    evidence_status: EvidenceStatus
    classification: SkillClassification


@dataclass(frozen=True)
class ProgressSummary:
    current_streak: int
    longest_streak: int
    total_study_days: int
    assigned_modules: int
    completed_modules: int
    completion_rate: float
    completed_planned_minutes: int
    tracked_seconds: int
    this_week_completed_planned_minutes: int
    completed_sessions: int
    skill_summaries: tuple[SkillProgressSummary, ...]
    recent_activity: tuple[DailyActivity, ...]
