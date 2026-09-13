import calendar
from datetime import date, timedelta
from zoneinfo import ZoneInfo

from app.domain.history.entities import StudyHistoryDay
from app.domain.learning_evidence.entities import Skill
from app.domain.resources.entities import LearningResourceDetails
from app.domain.study_plan.entities import StudyPlanItemStatus


SKILL_PRESENTATION = {
    Skill.LISTENING: ("LI", "精听 Listening"),
    Skill.SPEAKING: ("SP", "跟读与复述 Speaking"),
    Skill.READING: ("RE", "阅读 Reading"),
    Skill.VOCABULARY: ("VO", "词块与复习 Vocabulary"),
}
SYDNEY = ZoneInfo("Australia/Sydney")


def present_history_index(
    days: tuple[StudyHistoryDay, ...],
    today: date,
    selected_month: date,
    view: str,
    resources: dict[int, LearningResourceDetails],
) -> dict:
    records_by_date = {item.study_date: item for item in days}
    return {
        "active_page": "history",
        "view": view,
        "today": today,
        "selected_month": selected_month,
        "month_label": selected_month.strftime("%B %Y"),
        "previous_month": _shift_month(selected_month, -1).strftime("%Y-%m"),
        "next_month": _shift_month(selected_month, 1).strftime("%Y-%m"),
        "calendar_weeks": [
            [
                _present_calendar_day(value, selected_month.month, records_by_date)
                for value in week
            ]
            for week in calendar.Calendar(firstweekday=0).monthdatescalendar(
                selected_month.year,
                selected_month.month,
            )
        ],
        "timeline_days": tuple(
            _present_day(item, resources) for item in days
        ),
        "saved_day_count": len(days),
        "completed_module_count": sum(
            item.completed_module_count for item in days
        ),
        "session_count": sum(len(item.sessions) for item in days),
    }


def present_history_detail(
    day: StudyHistoryDay,
    resources: dict[int, LearningResourceDetails],
) -> dict:
    return {
        "active_page": "history",
        "day": _present_day(day, resources),
    }


def _present_day(
    day: StudyHistoryDay,
    resources: dict[int, LearningResourceDetails],
) -> dict:
    modules = []
    if day.plan:
        for item in day.plan.items:
            resource = resources.get(item.resource_id) if item.resource_id else None
            code, title = SKILL_PRESENTATION[item.skill]
            modules.append(
                {
                    "item": item,
                    "code": code,
                    "title": title,
                    "resource_title": resource.title if resource else "未指定材料",
                    "is_completed": item.status is StudyPlanItemStatus.COMPLETED,
                    "status_label": _status_label(item.status),
                    "started_at_label": _format_sydney_time(item.started_at),
                    "completed_at_label": _format_sydney_time(item.completed_at),
                }
            )
    return {
        "study_date": day.study_date,
        "display_date": day.study_date.strftime("%A · %d %B %Y"),
        "plan": day.plan,
        "modules": modules,
        "sessions": tuple(
            {
                "session": session,
                "skill_label": SKILL_PRESENTATION[session.skill][1],
                "accuracy_percent": round(session.accuracy * 100),
                "tracked_minutes": (
                    round(session.actual_duration_seconds / 60)
                    if session.actual_duration_seconds is not None
                    else None
                ),
            }
            for session in day.sessions
        ),
        "completed_module_count": day.completed_module_count,
        "assigned_module_count": day.assigned_module_count,
    }


def _present_calendar_day(
    value: date,
    selected_month: int,
    records_by_date: dict[date, StudyHistoryDay],
) -> dict:
    record = records_by_date.get(value)
    return {
        "date": value,
        "day_number": value.day,
        "in_month": value.month == selected_month,
        "has_record": record is not None,
        "completed_modules": record.completed_module_count if record else 0,
        "assigned_modules": record.assigned_module_count if record else 0,
        "session_count": len(record.sessions) if record else 0,
    }


def _shift_month(value: date, offset: int) -> date:
    anchor = value.replace(day=15) + timedelta(days=offset * 31)
    return anchor.replace(day=1)


def _status_label(status: StudyPlanItemStatus) -> str:
    return {
        StudyPlanItemStatus.PENDING: "未开始",
        StudyPlanItemStatus.IN_PROGRESS: "进行中",
        StudyPlanItemStatus.COMPLETED: "已完成",
    }[status]


def _format_sydney_time(value) -> str:
    if value is None:
        return "未记录"
    return value.astimezone(SYDNEY).strftime("%Y-%m-%d %H:%M")
