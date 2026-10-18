from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException

from app.api.frontend_dependencies import get_frontend_services
from app.api.learner_context import Learner
from app.composition import ApplicationServices
from app.domain.history.entities import StudyHistoryDay
from app.domain.learning_evidence.entities import Skill
from app.domain.learner_profile.entities import EvidenceStatus
from app.domain.study_plan.entities import StudyPlanItemStatus
from app.domain.weakness_detection.entities import SkillClassification
from app.schemas.frontend_insights import (
    DailyActivityResponse,
    HistoryDayResponse,
    HistoryModuleResponse,
    HistoryResponse,
    HistorySessionResponse,
    ProgressResponse,
    SkillProgressResponse,
    WeeklyAttemptSummaryResponse,
    WeeklyRecommendationResponse,
    WeeklyReviewResponse,
    WeeklySkillResponse,
)


router = APIRouter(prefix="/api/v1", tags=["frontend-insights"])
SYDNEY = ZoneInfo("Australia/Sydney")
SKILL_PRESENTATION = {
    Skill.LISTENING: ("LI", "听力 Listening"),
    Skill.SPEAKING: ("SP", "口语 Speaking"),
    Skill.READING: ("RE", "阅读 Reading"),
    Skill.WRITING: ("WR", "写作 Writing"),
    Skill.VOCABULARY: ("VO", "词汇 Vocabulary"),
}
EVIDENCE_LABELS = {
    EvidenceStatus.NO_DATA: "暂无证据",
    EvidenceStatus.PROVISIONAL: "暂定分数",
    EvidenceStatus.ESTABLISHED: "已建立",
}
CLASSIFICATION_LABELS = {
    SkillClassification.INSUFFICIENT_EVIDENCE: "数据不足",
    SkillClassification.WEAK: "薄弱",
    SkillClassification.DEVELOPING: "发展中",
    SkillClassification.STABLE: "稳定",
    SkillClassification.STRONG: "较强",
}


@router.get("/history", response_model=HistoryResponse)
def get_history(
    learner: Learner,
    view: str = "timeline",
    month: str | None = None,
    services: ApplicationServices = Depends(get_frontend_services),
) -> HistoryResponse:
    if view not in {"timeline", "calendar"}:
        raise HTTPException(status_code=422, detail="Invalid history view")
    today = datetime.now(SYDNEY).date()
    selected_month = _parse_month(month, today)
    days = (
        services.history.list_month(learner.user_key, selected_month)
        if view == "calendar"
        else services.history.list_recent_days(learner.user_key, today)
    )
    resources = _load_resources(days, services)
    responses = [_history_day(day, resources) for day in days]
    return HistoryResponse(
        today=today,
        selected_month=selected_month,
        month_label=selected_month.strftime("%B %Y"),
        previous_month=_shift_month(selected_month, -1).strftime("%Y-%m"),
        next_month=_shift_month(selected_month, 1).strftime("%Y-%m"),
        saved_day_count=len(days),
        completed_module_count=sum(day.completed_module_count for day in days),
        session_count=sum(len(day.sessions) for day in days),
        days=responses,
    )


@router.get("/history/{study_date}", response_model=HistoryDayResponse)
def get_history_day(
    study_date: date,
    learner: Learner,
    services: ApplicationServices = Depends(get_frontend_services),
) -> HistoryDayResponse:
    day = services.history.get_day(learner.user_key, study_date)
    if day is None:
        raise HTTPException(status_code=404, detail="Study history not found")
    return _history_day(day, _load_resources((day,), services))


@router.get("/progress", response_model=ProgressResponse)
def get_progress(
    learner: Learner,
    services: ApplicationServices = Depends(get_frontend_services),
) -> ProgressResponse:
    today = datetime.now(SYDNEY).date()
    summary = services.progress_analytics.get_summary(learner.user_key, today)
    return ProgressResponse(
        current_streak=summary.current_streak,
        longest_streak=summary.longest_streak,
        total_study_days=summary.total_study_days,
        assigned_modules=summary.assigned_modules,
        completed_modules=summary.completed_modules,
        completion_rate=summary.completion_rate,
        completed_planned_minutes=summary.completed_planned_minutes,
        tracked_seconds=summary.tracked_seconds,
        this_week_completed_planned_minutes=(
            summary.this_week_completed_planned_minutes
        ),
        completed_sessions=summary.completed_sessions,
        completed_reviews=summary.completed_reviews,
        skills=[
            SkillProgressResponse(
                skill=item.skill.value,
                code=SKILL_PRESENTATION[item.skill][0],
                label=SKILL_PRESENTATION[item.skill][1],
                completed_modules=item.completed_modules,
                completed_sessions=item.completed_sessions,
                score=round(item.profile_score) if item.profile_score is not None else None,
                evidence_status=item.evidence_status.value,
                evidence_label=EVIDENCE_LABELS[item.evidence_status],
                classification=item.classification.value,
                classification_label=CLASSIFICATION_LABELS[item.classification],
            )
            for item in summary.skill_summaries
        ],
        recent_activity=[
            DailyActivityResponse(
                activity_date=item.activity_date,
                assigned_modules=item.assigned_modules,
                completed_modules=item.completed_modules,
                completed_planned_minutes=item.completed_planned_minutes,
                completed_sessions=item.completed_sessions,
                tracked_seconds=item.tracked_seconds,
                activity_score=item.completed_modules + item.completed_sessions,
            )
            for item in summary.recent_activity
        ],
    )


@router.get("/weekly-review", response_model=WeeklyReviewResponse)
def get_weekly_review(
    learner: Learner,
    services: ApplicationServices = Depends(get_frontend_services),
) -> WeeklyReviewResponse:
    today = datetime.now(SYDNEY).date()
    review = services.weekly_review.get_current_week(learner.user_key, today)
    return WeeklyReviewResponse(
        week_start=review.week_start,
        week_end=review.week_end,
        date_range=(
            f"{review.week_start.strftime('%d %b')} — "
            f"{review.week_end.strftime('%d %b %Y')}"
        ),
        study_days=review.study_days,
        assigned_modules=review.assigned_modules,
        completed_modules=review.completed_modules,
        completion_rate=review.completion_rate,
        completed_planned_minutes=review.completed_planned_minutes,
        completed_sessions=review.completed_sessions,
        tracked_seconds=review.tracked_seconds,
        vocabulary_learned=review.vocabulary_learned,
        difficult_sentences_collected=review.difficult_sentences_collected,
        next_week_review_count=review.next_week_review_count,
        strongest_skill=(review.strongest_skill.value if review.strongest_skill else None),
        strongest_label=_skill_label(review.strongest_skill),
        weakest_skill=review.weakest_skill.value if review.weakest_skill else None,
        weakest_label=_skill_label(review.weakest_skill),
        review_attempts=WeeklyAttemptSummaryResponse(
            again_count=review.review_attempts.again_count,
            hard_count=review.review_attempts.hard_count,
            good_count=review.review_attempts.good_count,
            easy_count=review.review_attempts.easy_count,
            total_count=review.review_attempts.total_count,
            retention_rate=review.review_attempts.retention_rate,
        ),
        skills=[
            WeeklySkillResponse(
                skill=item.skill.value,
                code=SKILL_PRESENTATION[item.skill][0],
                label=SKILL_PRESENTATION[item.skill][1],
                completed_modules=item.completed_modules,
                completed_sessions=item.completed_sessions,
                average_accuracy_percent=(
                    round(item.average_accuracy * 100)
                    if item.average_accuracy is not None
                    else None
                ),
                incorrect_item_count=item.incorrect_item_count,
                tracked_seconds=item.tracked_seconds,
            )
            for item in review.skill_summaries
        ],
        recommendations=[
            WeeklyRecommendationResponse(
                title=item.title,
                reason=item.reason,
                href=item.href,
            )
            for item in review.recommendations
        ],
    )


def _history_day(day: StudyHistoryDay, resources) -> HistoryDayResponse:
    modules = []
    if day.plan:
        for item in day.plan.items:
            resource = resources.get(item.resource_id) if item.resource_id else None
            code, title = SKILL_PRESENTATION[item.skill]
            modules.append(
                HistoryModuleResponse(
                    item_id=item.id,
                    skill=item.skill.value,
                    code=code,
                    title=title,
                    resource_id=item.resource_id,
                    resource_title=resource.title if resource else "未指定材料",
                    planned_minutes=item.planned_minutes,
                    status=item.status.value,
                    completed=item.status is StudyPlanItemStatus.COMPLETED,
                    started_at=item.started_at,
                    completed_at=item.completed_at,
                )
            )
    sessions = [
        HistorySessionResponse(
            id=item.id,
            resource_id=item.resource_id,
            resource_title=item.resource_title,
            skill=item.skill.value,
            skill_label=SKILL_PRESENTATION[item.skill][1],
            status=item.status,
            completed_at=item.completed_at,
            actual_duration_seconds=item.actual_duration_seconds,
            accuracy_percent=(
                round(item.accuracy * 100) if item.accuracy is not None else None
            ),
            attempt_count=item.attempt_count,
            incorrect_item_count=item.incorrect_item_count,
            notes=item.notes,
        )
        for item in day.sessions
    ]
    return HistoryDayResponse(
        study_date=day.study_date,
        display_date=day.study_date.strftime("%A · %d %B %Y"),
        completed_module_count=day.completed_module_count,
        assigned_module_count=day.assigned_module_count,
        modules=modules,
        sessions=sessions,
    )


def _load_resources(days, services: ApplicationServices):
    resource_ids = {
        item.resource_id
        for day in days
        if day.plan
        for item in day.plan.items
        if item.resource_id is not None
    }
    return {
        resource_id: resource
        for resource_id in resource_ids
        if (resource := services.resources.get_resource(resource_id)) is not None
    }


def _parse_month(value: str | None, fallback: date) -> date:
    if value is None:
        return fallback.replace(day=1)
    try:
        return datetime.strptime(value, "%Y-%m").date().replace(day=1)
    except ValueError as error:
        raise HTTPException(status_code=422, detail="month must use YYYY-MM") from error


def _shift_month(value: date, offset: int) -> date:
    anchor = value.replace(day=15) + timedelta(days=offset * 31)
    return anchor.replace(day=1)


def _skill_label(skill: Skill | None) -> str:
    return SKILL_PRESENTATION[skill][1] if skill is not None else "证据不足"
