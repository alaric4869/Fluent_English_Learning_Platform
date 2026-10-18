from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from app.api.learner_context import Learner
from app.api.frontend_dependencies import get_frontend_services
from app.composition import ApplicationServices
from app.domain.adaptive_learning.entities import AdaptationDecision
from app.domain.learning_evidence.entities import Skill
from app.domain.resources.entities import LearningResourceDetails, ResourceCandidate
from app.domain.study_plan.config import SKILL_TIME_CONFIG
from app.domain.study_plan.entities import DailyStudyPlanItem
from app.domain.study_plan.entities import StudyPlanItemStatus
from app.domain.study_session.entities import ModuleStudySession
from app.presenters.today import MODULE_PRESENTATION
from app.schemas.frontend import (
    DashboardModuleResponse,
    DashboardResponse,
    DashboardStatsResponse,
    HealthResponse,
    ModuleSessionResponse,
    PlanRecommendationResponse,
    ResourceOptionResponse,
    TodayModuleResponse,
    TodayResponse,
)


router = APIRouter(prefix="/api/v1", tags=["frontend"])
SYDNEY = ZoneInfo("Australia/Sydney")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", api_version="v1")


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    learner: Learner,
    services: ApplicationServices = Depends(get_frontend_services),
) -> DashboardResponse:
    now = datetime.now(SYDNEY)
    snapshot = services.dashboard.get_snapshot(learner.user_key, now.date())
    resources = {
        item.resource_id: resource
        for item in snapshot.today_plan.items
        if item.resource_id is not None
        if (resource := services.resources.get_resource(item.resource_id)) is not None
    }
    completed_count = sum(
        item.status is StudyPlanItemStatus.COMPLETED
        for item in snapshot.today_plan.items
    )
    modules = [
        DashboardModuleResponse(
            item_id=item.id,
            skill=item.skill.value,
            code=MODULE_PRESENTATION[item.skill]["code"],
            title=MODULE_PRESENTATION[item.skill]["title"],
            planned_minutes=item.planned_minutes,
            status=item.status.value,
            resource_id=item.resource_id,
            resource_title=(
                resources[item.resource_id].title
                if item.resource_id in resources
                else "尚无匹配材料"
            ),
            completed=item.status is StudyPlanItemStatus.COMPLETED,
        )
        for item in snapshot.today_plan.items
    ]
    progress = snapshot.progress
    return DashboardResponse(
        greeting=_greeting(now.hour),
        display_date=now.strftime("%A · %d %B %Y"),
        plan_date=snapshot.today_plan.plan_date,
        plan_status=snapshot.today_plan.status.value,
        total_minutes=snapshot.today_plan.total_minutes,
        completed_count=completed_count,
        completion_percent=(
            round(completed_count / len(modules) * 100) if modules else 0
        ),
        due_review_count=snapshot.due_review_count,
        modules=modules,
        stats=DashboardStatsResponse(
            current_streak=progress.current_streak,
            longest_streak=progress.longest_streak,
            total_study_days=progress.total_study_days,
            completion_rate=progress.completion_rate,
            completed_sessions=progress.completed_sessions,
            completed_reviews=progress.completed_reviews,
            tracked_seconds=progress.tracked_seconds,
            this_week_completed_planned_minutes=(
                progress.this_week_completed_planned_minutes
            ),
        ),
    )


@router.get("/today", response_model=TodayResponse)
def get_today(
    learner: Learner,
    services: ApplicationServices = Depends(get_frontend_services),
) -> TodayResponse:
    now = datetime.now(SYDNEY)
    plan = services.study_plan.get_or_create_daily_plan(learner.user_key, now.date())
    recommendations = services.adaptation_decisions.get_pending_ai_recommendations(
        learner.user_key,
        plan.plan_date,
    )
    recommendation_by_item = {
        item.study_plan_item_id: item for item in recommendations
    }
    resource_ids = {
        resource_id
        for item in plan.items
        for resource_id in (item.resource_id,)
        if resource_id is not None
    }
    resource_ids.update(
        resource_id
        for item in recommendations
        for resource_id in (item.previous_resource_id, item.new_resource_id)
        if resource_id is not None
    )
    resources = {
        resource_id: services.resources.get_resource(resource_id)
        for resource_id in resource_ids
    }
    options = {
        skill: services.resources.list_available_for_skill(
            learner.user_key,
            skill,
            plan.plan_date,
        )
        for skill in Skill
    }
    sessions = services.study_sessions.get_latest_for_plan(
        learner.user_key,
        plan.plan_date,
    )
    modules = [
        _today_module(
            item=item,
            resource=resources.get(item.resource_id) if item.resource_id else None,
            options=options[item.skill],
            session=sessions.get(item.id),
            recommendation=recommendation_by_item.get(item.id),
            resources=resources,
        )
        for item in plan.items
    ]
    completed_count = sum(module.completed for module in modules)
    return TodayResponse(
        greeting=_greeting(now.hour),
        display_date=now.strftime("%A · %d %B %Y"),
        plan_id=plan.id,
        plan_date=plan.plan_date,
        plan_status=plan.status.value,
        total_minutes=plan.total_minutes,
        explanation=list(plan.explanation),
        completed_count=completed_count,
        completion_percent=(
            round(completed_count / len(modules) * 100) if modules else 0
        ),
        due_review_count=services.review.get_due_count(
            learner.user_key,
            plan.plan_date,
        ),
        agent_available=services.agent_planning.available,
        agent_unavailable_reason=services.agent_planning.unavailable_reason,
        modules=modules,
    )


def _today_module(
    *,
    item: DailyStudyPlanItem,
    resource: LearningResourceDetails | None,
    options: tuple[ResourceCandidate, ...],
    session: ModuleStudySession | None,
    recommendation: AdaptationDecision | None,
    resources: dict[int, LearningResourceDetails | None],
) -> TodayModuleResponse:
    presentation = MODULE_PRESENTATION[item.skill]
    time_config = SKILL_TIME_CONFIG[item.skill]
    return TodayModuleResponse(
        item_id=item.id,
        skill=item.skill.value,
        code=presentation["code"],
        title=presentation["title"],
        instruction=presentation["instruction"],
        objective=presentation["objective"],
        planned_minutes=item.planned_minutes,
        minimum_minutes=time_config.minimum_minutes,
        maximum_minutes=time_config.maximum_minutes,
        status=item.status.value,
        resource_id=item.resource_id,
        resource_title=resource.title if resource else "尚无匹配材料",
        resource_meta=(
            " · ".join(
                part
                for part in (resource.topic, resource.difficulty or "难度未标注")
                if part
            )
            if resource
            else "材料库补充后会自动匹配"
        ),
        start_href=_resource_href(resource),
        completed=item.status is StudyPlanItemStatus.COMPLETED,
        reasons=list(item.reasons),
        options=[
            ResourceOptionResponse(
                id=option.id,
                title=option.title,
                difficulty=option.difficulty,
                estimated_duration_minutes=option.estimated_duration_minutes,
            )
            for option in options
        ],
        session=ModuleSessionResponse(
            id=session.id if session else None,
            status=session.status.value if session else "not_started",
            active_duration_seconds=(session.active_duration_seconds if session else 0),
            notes=session.notes if session else "",
            perceived_difficulty=session.perceived_difficulty if session else None,
            confidence=session.confidence if session else None,
            completed=(session.status.value == "completed" if session else False),
        ),
        ai_recommendation=_recommendation(item, recommendation, resources),
    )


def _recommendation(
    item: DailyStudyPlanItem,
    recommendation: AdaptationDecision | None,
    resources: dict[int, LearningResourceDetails | None],
) -> PlanRecommendationResponse | None:
    if recommendation is None:
        return None
    current = resources.get(recommendation.previous_resource_id)
    proposed = resources.get(recommendation.new_resource_id)
    return PlanRecommendationResponse(
        id=recommendation.id,
        current_minutes=recommendation.previous_planned_minutes,
        proposed_minutes=recommendation.new_planned_minutes,
        current_resource_title=current.title if current else "暂不指定材料",
        proposed_resource_title=proposed.title if proposed else "暂不指定材料",
        resource_changed=(
            recommendation.previous_resource_id != recommendation.new_resource_id
        ),
        minutes_changed=(
            recommendation.previous_planned_minutes
            != recommendation.new_planned_minutes
        ),
        stale=(
            item.planned_minutes != recommendation.previous_planned_minutes
            or item.resource_id != recommendation.previous_resource_id
        ),
        reasons=[
            reason
            for reason in recommendation.reasons
            if not reason.startswith("AI provider:")
            and reason != "This recommendation has not changed the learner's plan."
        ],
    )


def _resource_href(resource: LearningResourceDetails | None) -> str | None:
    if resource is None:
        return None
    if resource.skill.value in {"listening", "speaking", "writing"}:
        return f"/{resource.skill.value}/{resource.id}"
    slug = resource.content.get("practice_set_slug")
    if isinstance(slug, str) and slug:
        return f"/ielts/{slug}"
    return resource.source_url


def _greeting(hour: int) -> str:
    if hour < 12:
        return "早上好"
    if hour < 18:
        return "下午好"
    return "晚上好"
