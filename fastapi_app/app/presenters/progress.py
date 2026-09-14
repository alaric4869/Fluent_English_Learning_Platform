from app.domain.analytics.entities import ProgressSummary
from app.domain.learning_evidence.entities import Skill
from app.domain.learner_profile.entities import EvidenceStatus
from app.domain.weakness_detection.entities import SkillClassification


SKILL_PRESENTATION = {
    Skill.LISTENING: ("LI", "听力 Listening"),
    Skill.SPEAKING: ("SP", "口语 Speaking"),
    Skill.READING: ("RE", "阅读 Reading"),
    Skill.WRITING: ("WR", "写作 Writing"),
    Skill.VOCABULARY: ("VO", "词汇 Vocabulary"),
}

CLASSIFICATION_LABELS = {
    SkillClassification.INSUFFICIENT_EVIDENCE: "数据不足",
    SkillClassification.WEAK: "薄弱",
    SkillClassification.DEVELOPING: "发展中",
    SkillClassification.STABLE: "稳定",
    SkillClassification.STRONG: "较强",
}

EVIDENCE_LABELS = {
    EvidenceStatus.NO_DATA: "暂无证据",
    EvidenceStatus.PROVISIONAL: "暂定分数",
    EvidenceStatus.ESTABLISHED: "已建立",
}


def present_progress(summary: ProgressSummary) -> dict:
    maximum_activity = max(
        (
            item.completed_modules + item.completed_sessions
            for item in summary.recent_activity
        ),
        default=1,
    ) or 1
    return {
        "active_page": "progress",
        "summary": summary,
        "completed_planned_time": _format_minutes(
            summary.completed_planned_minutes
        ),
        "tracked_time": _format_seconds(summary.tracked_seconds),
        "this_week_planned_time": _format_minutes(
            summary.this_week_completed_planned_minutes
        ),
        "skill_summaries": tuple(
            {
                "skill": item.skill,
                "code": SKILL_PRESENTATION[item.skill][0],
                "label": SKILL_PRESENTATION[item.skill][1],
                "score": round(item.profile_score) if item.profile_score is not None else None,
                "evidence_label": EVIDENCE_LABELS[item.evidence_status],
                "classification_label": CLASSIFICATION_LABELS[item.classification],
            }
            | {"summary": item}
            for item in summary.skill_summaries
        ),
        "recent_activity": tuple(
            {
                "activity": item,
                "height_percent": round(
                    (item.completed_modules + item.completed_sessions)
                    / maximum_activity
                    * 100
                ),
                "label": item.activity_date.strftime("%d %b"),
            }
            for item in summary.recent_activity
        ),
    }


def _format_minutes(value: int) -> str:
    hours, minutes = divmod(value, 60)
    if hours and minutes:
        return f"{hours}h {minutes}m"
    if hours:
        return f"{hours}h"
    return f"{minutes}m"


def _format_seconds(value: int) -> str:
    return _format_minutes(round(value / 60))
