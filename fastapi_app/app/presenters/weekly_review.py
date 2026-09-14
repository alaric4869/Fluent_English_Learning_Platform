from app.domain.learning_evidence.entities import Skill
from app.domain.weekly_review.entities import WeeklyReview


SKILL_PRESENTATION = {
    Skill.LISTENING: ("LI", "听力 Listening"),
    Skill.SPEAKING: ("SP", "口语 Speaking"),
    Skill.READING: ("RE", "阅读 Reading"),
    Skill.VOCABULARY: ("VO", "词汇 Vocabulary"),
}


def present_weekly_review(review: WeeklyReview) -> dict:
    return {
        "active_page": "dashboard",
        "review": review,
        "date_range": (
            f"{review.week_start.strftime('%d %b')} — "
            f"{review.week_end.strftime('%d %b %Y')}"
        ),
        "tracked_time": _format_seconds(review.tracked_seconds),
        "completed_planned_time": _format_minutes(
            review.completed_planned_minutes
        ),
        "retention_label": (
            f"{review.review_attempts.retention_rate}%"
            if review.review_attempts.retention_rate is not None
            else "—"
        ),
        "strongest_label": _skill_label(review.strongest_skill),
        "weakest_label": _skill_label(review.weakest_skill),
        "skills": tuple(
            {
                "summary": item,
                "code": SKILL_PRESENTATION[item.skill][0],
                "label": SKILL_PRESENTATION[item.skill][1],
                "accuracy_label": (
                    f"{round(item.average_accuracy * 100)}%"
                    if item.average_accuracy is not None
                    else "—"
                ),
                "accuracy_percent": (
                    round(item.average_accuracy * 100)
                    if item.average_accuracy is not None
                    else 0
                ),
                "tracked_time": _format_seconds(item.tracked_seconds),
            }
            for item in review.skill_summaries
        ),
    }


def _skill_label(skill: Skill | None) -> str:
    return SKILL_PRESENTATION[skill][1] if skill is not None else "证据不足"


def _format_minutes(value: int) -> str:
    hours, minutes = divmod(value, 60)
    if hours and minutes:
        return f"{hours}h {minutes}m"
    if hours:
        return f"{hours}h"
    return f"{minutes}m"


def _format_seconds(value: int) -> str:
    return _format_minutes(round(value / 60))
