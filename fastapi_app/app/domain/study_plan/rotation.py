from datetime import date

from app.domain.learning_evidence.entities import Skill


def daily_plan_skills(plan_date: date) -> tuple[Skill, ...]:
    """Keep four daily modules while alternating input and output practice."""
    literacy_skill = (
        Skill.READING if plan_date.toordinal() % 2 else Skill.WRITING
    )
    return (
        Skill.LISTENING,
        Skill.SPEAKING,
        literacy_skill,
        Skill.VOCABULARY,
    )
