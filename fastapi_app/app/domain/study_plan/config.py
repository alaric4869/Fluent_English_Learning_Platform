from dataclasses import dataclass

from app.domain.learning_evidence.entities import Skill


@dataclass(frozen=True)
class SkillTimeConfig:
    default_minutes: int
    minimum_minutes: int
    maximum_minutes: int


@dataclass(frozen=True)
class StudyPlanConfig:
    generator_version: str = "rule-based-v1"
    maximum_total_minutes: int = 120
    weak_adjustment_minutes: int = 10
    developing_adjustment_minutes: int = 5
    strong_adjustment_minutes: int = -5


SKILL_TIME_CONFIG = {
    Skill.LISTENING: SkillTimeConfig(30, 15, 45),
    Skill.SPEAKING: SkillTimeConfig(25, 15, 40),
    Skill.READING: SkillTimeConfig(30, 15, 45),
    Skill.VOCABULARY: SkillTimeConfig(25, 15, 40),
}

DEFAULT_STUDY_PLAN_CONFIG = StudyPlanConfig()
