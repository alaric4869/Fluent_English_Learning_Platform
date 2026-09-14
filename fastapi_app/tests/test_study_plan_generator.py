from datetime import date

from app.domain.learning_evidence.entities import Skill
from app.domain.study_plan.entities import SkillPlanningSignal, StudyPlanGenerationContext
from app.domain.study_plan.rule_based_generator import RuleBasedStudyPlanGenerator
from app.domain.study_plan.rotation import daily_plan_skills
from app.domain.weakness_detection.entities import SkillClassification


PLAN_DATE = date(2026, 9, 14)


def test_no_evidence_uses_the_default_110_minute_plan() -> None:
    plan = RuleBasedStudyPlanGenerator().generate(
        _context(
            {
                skill: SkillClassification.INSUFFICIENT_EVIDENCE
                for skill in daily_plan_skills(PLAN_DATE)
            }
        )
    )

    assert plan.total_minutes == 110
    assert [item.planned_minutes for item in plan.items] == [30, 25, 30, 25]
    assert all(item.resource_id is None for item in plan.items)


def test_confirmed_weakness_increases_time_and_strength_reduces_it_gradually() -> None:
    plan = RuleBasedStudyPlanGenerator().generate(
        _context(
            {
                Skill.LISTENING: SkillClassification.WEAK,
                Skill.SPEAKING: SkillClassification.STABLE,
                Skill.READING: SkillClassification.STRONG,
                Skill.VOCABULARY: SkillClassification.STABLE,
            }
        )
    )

    assert plan.total_minutes == 115
    assert [item.planned_minutes for item in plan.items] == [40, 25, 25, 25]
    listening = plan.items[0]
    assert any("从默认 30 分钟增加到 40 分钟" in reason for reason in listening.reasons)
    assert "真实评估原因" in listening.reasons


def test_daily_cap_reduces_only_the_adaptive_increment() -> None:
    plan = RuleBasedStudyPlanGenerator().generate(
        _context(
            {
                skill: SkillClassification.WEAK
                for skill in daily_plan_skills(PLAN_DATE)
            }
        )
    )

    assert plan.total_minutes == 120
    assert all(
        item.planned_minutes >= default
        for item, default in zip(plan.items, [30, 25, 30, 25], strict=True)
    )
    assert any("每日上限 120 分钟" in reason for reason in plan.explanation)


def _context(
    classifications: dict[Skill, SkillClassification],
) -> StudyPlanGenerationContext:
    return StudyPlanGenerationContext(
        user_key="learner",
        plan_date=PLAN_DATE,
        weakness_assessment_run_id=1,
        recommender_version="test-recommender",
        skill_signals=tuple(
            SkillPlanningSignal(
                skill=skill,
                classification=classifications[skill],
                assessment_reasons=("真实评估原因",),
                resource_recommendation=None,
            )
            for skill in daily_plan_skills(PLAN_DATE)
        ),
    )


def test_reading_and_writing_rotate_without_adding_a_fifth_daily_module() -> None:
    assert daily_plan_skills(date(2026, 9, 14)) == (
        Skill.LISTENING,
        Skill.SPEAKING,
        Skill.READING,
        Skill.VOCABULARY,
    )
    assert daily_plan_skills(date(2026, 9, 15)) == (
        Skill.LISTENING,
        Skill.SPEAKING,
        Skill.WRITING,
        Skill.VOCABULARY,
    )
