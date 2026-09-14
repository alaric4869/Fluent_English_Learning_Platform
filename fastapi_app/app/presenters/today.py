from datetime import datetime
from urllib.parse import urlparse

from app.domain.learning_evidence.entities import Skill
from app.domain.resources.entities import LearningResourceDetails, ResourceCandidate
from app.domain.study_plan.config import SKILL_TIME_CONFIG
from app.domain.study_plan.entities import DailyStudyPlan, StudyPlanItemStatus
from app.domain.study_session.entities import ModuleStudySession, StudySessionStatus


MODULE_PRESENTATION = {
    Skill.LISTENING: {
        "code": "LI",
        "title": "精听 Listening",
        "instruction": "第一遍不看文本；第二遍对照英文；逐句定位听不清的内容；最后再裸听一次。",
        "objective": "提高真实语速下的句子识别与自然口语理解。",
    },
    Skill.SPEAKING: {
        "code": "SP",
        "title": "跟读与复述 Speaking",
        "instruction": "听一句、暂停、模仿；随后隐藏文本，用自己的英语复述主要内容。",
        "objective": "建立自然语音节奏、反应速度和连续表达。",
    },
    Skill.READING: {
        "code": "RE",
        "title": "阅读 Reading",
        "instruction": "先在限定时间内完成材料；只查影响理解的词，并记录可复用的完整表达。",
        "objective": "提高定位、理解和 IELTS G 阅读准确率。",
    },
    Skill.VOCABULARY: {
        "code": "VO",
        "title": "词块与复习 Vocabulary",
        "instruction": "优先复习到期内容，再学习少量完整词块，并用自己的句子主动输出。",
        "objective": "提高长期记忆和真实交流中的主动调用能力。",
    },
}


def present_today_plan(
    plan: DailyStudyPlan,
    now: datetime,
    resources: dict[int, LearningResourceDetails],
    resource_options: dict[Skill, tuple[ResourceCandidate, ...]],
    due_review_count: int = 0,
    sessions: dict[int, ModuleStudySession] | None = None,
) -> dict:
    sessions = sessions or {}
    completed_count = sum(
        item.status is StudyPlanItemStatus.COMPLETED for item in plan.items
    )
    return {
        "active_page": "today",
        "greeting": _greeting(now.hour),
        "display_date": now.strftime("%A · %d %B %Y"),
        "plan": plan,
        "completed_count": completed_count,
        "completion_percent": round(completed_count / len(plan.items) * 100)
        if plan.items
        else 0,
        "due_review_count": due_review_count,
        "modules": [
            _present_module(
                item,
                resources,
                resource_options.get(item.skill, ()),
                sessions.get(item.id),
            )
            for item in plan.items
        ],
    }


def present_plan_response(plan: DailyStudyPlan) -> dict:
    return {
        "id": plan.id,
        "plan_date": plan.plan_date,
        "status": plan.status,
        "total_minutes": plan.total_minutes,
        "items": [
            {
                "id": item.id,
                "skill": item.skill,
                "system_planned_minutes": item.system_planned_minutes,
                "planned_minutes": item.planned_minutes,
                "system_resource_id": item.system_resource_id,
                "resource_id": item.resource_id,
                "status": item.status,
                "manual_override": item.manual_override,
                "started_at": item.started_at,
                "completed_at": item.completed_at,
            }
            for item in plan.items
        ],
    }


def _present_module(
    item,
    resources: dict[int, LearningResourceDetails],
    options: tuple[ResourceCandidate, ...],
    session: ModuleStudySession | None,
) -> dict:
    resource = resources.get(item.resource_id) if item.resource_id else None
    presentation = MODULE_PRESENTATION[item.skill]
    time_config = SKILL_TIME_CONFIG[item.skill]
    return {
        "item": item,
        **presentation,
        "resource_title": resource.title if resource else "尚无匹配材料",
        "resource_meta": _resource_meta(resource),
        "start_href": _resource_href(resource),
        "options": options,
        "minimum_minutes": time_config.minimum_minutes,
        "maximum_minutes": time_config.maximum_minutes,
        "is_completed": item.status is StudyPlanItemStatus.COMPLETED,
        "session": _present_session(session),
    }


def _resource_meta(resource: LearningResourceDetails | None) -> str:
    if resource is None:
        return "材料库补充后会自动匹配"
    parts = [resource.topic, resource.difficulty or "难度未标注"]
    return " · ".join(part for part in parts if part)


def _resource_href(resource: LearningResourceDetails | None) -> str | None:
    if resource is None:
        return None
    if resource.skill is Skill.LISTENING:
        return f"/listening/{resource.id}"
    practice_slug = resource.content.get("practice_set_slug")
    if isinstance(practice_slug, str) and practice_slug:
        return f"/ielts/{practice_slug}"
    if resource.source_url:
        parsed = urlparse(resource.source_url)
        if parsed.scheme in {"http", "https"}:
            return resource.source_url
    return None


def _present_session(session: ModuleStudySession | None) -> dict:
    if session is None:
        return {
            "id": "",
            "status": "not_started",
            "active_duration_seconds": 0,
            "notes": "",
            "perceived_difficulty": None,
            "confidence": None,
            "is_completed": False,
        }
    return {
        "id": session.id,
        "status": session.status.value,
        "active_duration_seconds": session.active_duration_seconds,
        "notes": session.notes,
        "perceived_difficulty": session.perceived_difficulty,
        "confidence": session.confidence,
        "is_completed": session.status is StudySessionStatus.COMPLETED,
    }


def _greeting(hour: int) -> str:
    if hour < 12:
        return "早上好"
    if hour < 18:
        return "下午好"
    return "晚上好"
