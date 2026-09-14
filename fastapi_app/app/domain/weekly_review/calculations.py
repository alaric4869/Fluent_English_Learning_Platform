from datetime import date, timedelta

from app.domain.learning_evidence.entities import Skill
from app.domain.weekly_review.entities import WeeklySkillSummary


def week_range(value: date) -> tuple[date, date]:
    """Return the learner-local Monday and exclusive next Monday."""
    start = value - timedelta(days=value.weekday())
    return start, start + timedelta(days=7)


def select_skill_highlights(
    summaries: tuple[WeeklySkillSummary, ...],
) -> tuple[Skill | None, Skill | None]:
    measured = tuple(item for item in summaries if item.average_accuracy is not None)
    if not measured:
        return None, None
    strongest = max(measured, key=lambda item: item.average_accuracy or 0).skill
    weakest = (
        min(measured, key=lambda item: item.average_accuracy or 0).skill
        if len(measured) > 1
        else None
    )
    return strongest, weakest
