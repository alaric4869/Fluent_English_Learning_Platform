from zoneinfo import ZoneInfo

from app.domain.agent_coaching.entities import WeeklyCoachingReport


SYDNEY = ZoneInfo("Australia/Sydney")

TOOL_LABELS = {
    "generate_weekly_report": "本周学习数据",
    "get_skill_profile": "技能画像",
    "get_weak_skills": "强弱项判断",
    "get_due_reviews": "到期复习",
}


def present_weekly_coaching_report(
    report: WeeklyCoachingReport | None,
) -> dict | None:
    if report is None:
        return None
    return {
        "id": report.id,
        "week_start": report.draft.week_start,
        "provider_name": report.draft.provider_name,
        "output_text": report.draft.output_text,
        "tools_used": tuple(
            TOOL_LABELS.get(item.value, item.value) for item in report.draft.tools_used
        ),
        "created_label": report.created_at.astimezone(SYDNEY).strftime(
            "%d %b %Y · %H:%M"
        ),
    }


def present_weekly_coaching_response(report: WeeklyCoachingReport) -> dict:
    return {
        "id": report.id,
        "week_start": report.draft.week_start,
        "provider_name": report.draft.provider_name,
        "output_text": report.draft.output_text,
        "tools_used": report.draft.tools_used,
        "created_at": report.created_at,
    }
