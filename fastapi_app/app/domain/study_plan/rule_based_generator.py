from app.domain.learning_evidence.entities import Skill
from app.domain.study_plan.config import (
    DEFAULT_STUDY_PLAN_CONFIG,
    SKILL_TIME_CONFIG,
    StudyPlanConfig,
)
from app.domain.study_plan.entities import (
    SkillPlanningSignal,
    StudyPlanGenerationContext,
    StudyPlanItemProposal,
    StudyPlanProposal,
)
from app.domain.weakness_detection.entities import SkillClassification


SKILL_LABELS = {
    Skill.LISTENING: "听力",
    Skill.SPEAKING: "口语",
    Skill.READING: "阅读",
    Skill.VOCABULARY: "词汇与复习",
}


class RuleBasedStudyPlanGenerator:
    def __init__(
        self,
        config: StudyPlanConfig = DEFAULT_STUDY_PLAN_CONFIG,
    ) -> None:
        self.config = config

    @property
    def generator_version(self) -> str:
        return self.config.generator_version

    def generate(self, context: StudyPlanGenerationContext) -> StudyPlanProposal:
        signals = {item.skill: item for item in context.skill_signals}
        planned_minutes = {
            skill: self._desired_minutes(signals.get(skill)) for skill in Skill
        }
        capped_skills = self._cap_total(planned_minutes, signals)
        items = tuple(
            self._build_item(
                skill,
                position,
                planned_minutes[skill],
                signals.get(skill),
                skill in capped_skills,
            )
            for position, skill in enumerate(Skill, start=1)
        )
        total_minutes = sum(item.planned_minutes for item in items)
        cap_explanation = (
            (f"总时长受每日上限 {self.config.maximum_total_minutes} 分钟约束。",)
            if capped_skills
            else ()
        )
        explanation = (
            f"计划由 {self.generator_version} 生成，总时长 {total_minutes} 分钟。",
            *cap_explanation,
        )
        return StudyPlanProposal(
            user_key=context.user_key,
            plan_date=context.plan_date,
            source="rule_based",
            generator_version=self.generator_version,
            weakness_assessment_run_id=context.weakness_assessment_run_id,
            recommender_version=context.recommender_version,
            total_minutes=total_minutes,
            explanation=explanation,
            items=items,
        )

    def _desired_minutes(self, signal: SkillPlanningSignal | None) -> int:
        skill = signal.skill if signal else None
        if skill is None:
            raise ValueError("Every study-plan skill requires a planning signal")
        time_config = SKILL_TIME_CONFIG[skill]
        adjustment = {
            SkillClassification.WEAK: self.config.weak_adjustment_minutes,
            SkillClassification.DEVELOPING: self.config.developing_adjustment_minutes,
            SkillClassification.STRONG: self.config.strong_adjustment_minutes,
        }.get(signal.classification, 0)
        return min(
            time_config.maximum_minutes,
            max(time_config.minimum_minutes, time_config.default_minutes + adjustment),
        )

    def _cap_total(
        self,
        planned_minutes: dict[Skill, int],
        signals: dict[Skill, SkillPlanningSignal],
    ) -> set[Skill]:
        excess = sum(planned_minutes.values()) - self.config.maximum_total_minutes
        if excess <= 0:
            return set()
        reduction_order = sorted(
            Skill,
            key=lambda skill: (
                _adaptation_priority(signals[skill].classification),
                list(Skill).index(skill),
            ),
        )
        capped: set[Skill] = set()
        while excess > 0:
            changed = False
            for skill in reduction_order:
                default = SKILL_TIME_CONFIG[skill].default_minutes
                if planned_minutes[skill] <= default:
                    continue
                planned_minutes[skill] -= 1
                excess -= 1
                changed = True
                capped.add(skill)
                if excess == 0:
                    break
            if not changed:
                break
        return capped

    def _build_item(
        self,
        skill: Skill,
        position: int,
        minutes: int,
        signal: SkillPlanningSignal | None,
        capped: bool,
    ) -> StudyPlanItemProposal:
        if signal is None:
            raise ValueError("Every study-plan skill requires a planning signal")
        default = SKILL_TIME_CONFIG[skill].default_minutes
        reasons = [
            _duration_reason(skill, default, minutes, signal.classification),
            *signal.assessment_reasons,
        ]
        if capped:
            reasons.append(
                f"为保持每日计划不超过 {self.config.maximum_total_minutes} 分钟，"
                "本模块的增量被小幅收紧。"
            )
        recommendation = signal.resource_recommendation
        if recommendation is None:
            reasons.append("当前没有可用的匹配资源；计划保留模块位置，等待补充材料。")
        else:
            reasons.extend(recommendation.reasons)
        return StudyPlanItemProposal(
            skill=skill,
            position=position,
            planned_minutes=minutes,
            resource_id=recommendation.resource_id if recommendation else None,
            recommendation_score=recommendation.score if recommendation else None,
            reasons=tuple(reasons),
        )


def _adaptation_priority(classification: SkillClassification) -> int:
    return {
        SkillClassification.DEVELOPING: 0,
        SkillClassification.STABLE: 1,
        SkillClassification.INSUFFICIENT_EVIDENCE: 2,
        SkillClassification.STRONG: 3,
        SkillClassification.WEAK: 4,
    }[classification]


def _duration_reason(
    skill: Skill,
    default: int,
    planned: int,
    classification: SkillClassification,
) -> str:
    label = SKILL_LABELS[skill]
    if planned == default:
        return f"{label}保持默认 {default} 分钟；当前状态为 {classification.value}。"
    direction = "增加" if planned > default else "减少"
    return (
        f"{label}从默认 {default} 分钟{direction}到 {planned} 分钟，"
        f"因为当前状态为 {classification.value}。"
    )
