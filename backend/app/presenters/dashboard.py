from datetime import datetime

from app.domain.dashboard.entities import DashboardSnapshot
from app.domain.resources.entities import LearningResourceDetails
from app.domain.study_plan.entities import StudyPlanItemStatus
from app.presenters.today import MODULE_PRESENTATION


def present_dashboard(
    snapshot: DashboardSnapshot,
    now: datetime,
    resources: dict[int, LearningResourceDetails],
) -> dict:
    plan = snapshot.today_plan
    completed_count = sum(
        item.status is StudyPlanItemStatus.COMPLETED for item in plan.items
    )
    return {
        "active_page": "dashboard",
        "greeting": _greeting(now.hour),
        "display_date": now.strftime("%A · %d %B %Y"),
        "plan": plan,
        "modules": tuple(
            {
                "item": item,
                "code": MODULE_PRESENTATION[item.skill]["code"],
                "title": MODULE_PRESENTATION[item.skill]["title"],
                "resource_title": (
                    resources[item.resource_id].title
                    if item.resource_id in resources
                    else "尚无匹配材料"
                ),
                "is_completed": item.status is StudyPlanItemStatus.COMPLETED,
            }
            for item in plan.items
        ),
        "completed_count": completed_count,
        "completion_percent": (
            round(completed_count / len(plan.items) * 100) if plan.items else 0
        ),
        "due_review_count": snapshot.due_review_count,
        "progress": snapshot.progress,
        "weekly": snapshot.weekly_review,
        "weekly_tracked_time": _format_seconds(
            snapshot.weekly_review.tracked_seconds
        ),
        "weekly_planned_time": _format_minutes(
            snapshot.weekly_review.completed_planned_minutes
        ),
    }


def _greeting(hour: int) -> str:
    if hour < 12:
        return "早上好"
    if hour < 18:
        return "下午好"
    return "晚上好"


def _format_minutes(value: int) -> str:
    hours, minutes = divmod(value, 60)
    if hours and minutes:
        return f"{hours}h {minutes}m"
    if hours:
        return f"{hours}h"
    return f"{minutes}m"


def _format_seconds(value: int) -> str:
    return _format_minutes(round(value / 60))
