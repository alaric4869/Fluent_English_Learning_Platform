from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.learner_context import Learner
from app.composition import ApplicationServices, build_application_services
from app.config import FASTAPI_ROOT
from app.database import get_db
from app.domain.adaptive_learning.entities import AIRecommendationAction
from app.domain.adaptive_learning.repository import (
    AIRecommendationAlreadyRespondedError,
    StaleStudyPlanOverrideError,
)
from app.domain.learning_evidence.entities import Skill
from app.domain.study_session.entities import StudySessionProgress
from app.presenters.today import present_plan_response, present_today_plan
from app.schemas.study_plan import (
    AIRecommendationResponseRequest,
    AgentPlanRecommendationResponse,
    PlanItemOverrideRequest,
    PlanItemStatusRequest,
    StudyPlanResponse,
)
from app.schemas.study_session import (
    ModuleStudySessionResponse,
    StudySessionProgressRequest,
)
from app.services.adaptive_learning import (
    InvalidPlanOverrideError,
    StaleAIRecommendationError,
)
from app.services.agent_planning import (
    AgentPlanningGenerationError,
    AgentPlanningUnavailableError,
)
from app.services.study_session import InvalidStudySessionError


router = APIRouter()
templates = Jinja2Templates(directory=FASTAPI_ROOT / "app" / "templates")
SYDNEY = ZoneInfo("Australia/Sydney")


def get_services(session: Session = Depends(get_db)) -> ApplicationServices:
    return build_application_services(session)


@router.get("/today")
def today_page(
    request: Request,
    learner: Learner,
    services: ApplicationServices = Depends(get_services),
):
    now = datetime.now(SYDNEY)
    plan = services.study_plan.get_or_create_daily_plan(learner.user_key, now.date())
    ai_recommendations = (
        services.adaptation_decisions.get_pending_ai_recommendations(
            learner.user_key, plan.plan_date
        )
    )
    resource_ids = {
        resource_id
        for item in plan.items
        for resource_id in (item.resource_id,)
        if resource_id is not None
    }
    resource_ids.update(
        resource_id
        for recommendation in ai_recommendations
        for resource_id in (
            recommendation.previous_resource_id,
            recommendation.new_resource_id,
        )
        if resource_id is not None
    )
    resources = {
        resource_id: services.resources.get_resource(resource_id)
        for resource_id in resource_ids
    }
    resource_options = {
        skill: services.resources.list_available_for_skill(
            learner.user_key,
            skill,
            plan.plan_date,
        )
        for skill in Skill
    }
    context = present_today_plan(
        plan,
        now,
        resources,
        resource_options,
        services.review.get_due_count(learner.user_key, now.date()),
        services.study_sessions.get_latest_for_plan(
            learner.user_key, plan.plan_date
        ),
        ai_recommendations,
    )
    context.update(
        {
            "agent_plan_available": services.agent_planning.available,
            "agent_plan_unavailable_reason": (
                services.agent_planning.unavailable_reason
            ),
        }
    )
    return templates.TemplateResponse(
        request=request,
        name="today/index.html",
        context=context,
    )


@router.post(
    "/api/agent/plan-recommendations",
    response_model=AgentPlanRecommendationResponse,
)
def generate_ai_plan_recommendations(
    learner: Learner,
    services: ApplicationServices = Depends(get_services),
):
    today = datetime.now(SYDNEY).date()
    try:
        result = services.agent_planning.generate_recommendations(
            learner.user_key, today
        )
    except AgentPlanningUnavailableError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except AgentPlanningGenerationError as error:
        raise HTTPException(
            status_code=502,
            detail="AI 服务暂时无法生成计划建议，请稍后重试。",
        ) from error
    return AgentPlanRecommendationResponse(
        output_text=result.output_text,
        tools_used=result.tools_used,
        pending_count=result.pending_count,
    )


@router.post(
    "/api/study-plans/{plan_date}/ai-recommendations/{recommendation_id}/respond",
    response_model=StudyPlanResponse,
)
def respond_to_ai_plan_recommendation(
    plan_date: date,
    recommendation_id: int,
    payload: AIRecommendationResponseRequest,
    learner: Learner,
    services: ApplicationServices = Depends(get_services),
):
    try:
        recommendation = next(
            (
                item
                for item in services.adaptation_decisions.get_pending_ai_recommendations(
                    learner.user_key, plan_date
                )
                if item.id == recommendation_id
            ),
            None,
        )
        if recommendation is None:
            raise LookupError("Pending AI recommendation not found")
        if payload.action is AIRecommendationAction.ACCEPT:
            services.study_sessions.validate_resource_override(
                learner.user_key,
                plan_date,
                recommendation.study_plan_item_id,
                recommendation.new_resource_id,
            )
        plan = services.adaptation_decisions.respond_to_ai_recommendation(
            learner.user_key,
            plan_date,
            recommendation_id,
            action=payload.action,
            note=payload.note,
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except (
        AIRecommendationAlreadyRespondedError,
        StaleAIRecommendationError,
        StaleStudyPlanOverrideError,
    ) as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except (InvalidPlanOverrideError, InvalidStudySessionError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return present_plan_response(plan)


@router.post(
    "/api/study-plans/{plan_date}/items/{study_plan_item_id}/sessions",
    response_model=ModuleStudySessionResponse,
)
def start_study_session(
    plan_date: date,
    study_plan_item_id: int,
    learner: Learner,
    services: ApplicationServices = Depends(get_services),
):
    try:
        return services.study_sessions.start(
            learner.user_key, plan_date, study_plan_item_id
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidStudySessionError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.patch(
    "/api/study-plans/{plan_date}/items/{study_plan_item_id}/sessions/{study_session_id}",
    response_model=ModuleStudySessionResponse,
)
def save_study_session(
    plan_date: date,
    study_plan_item_id: int,
    study_session_id: int,
    payload: StudySessionProgressRequest,
    learner: Learner,
    services: ApplicationServices = Depends(get_services),
):
    try:
        return services.study_sessions.save_progress(
            learner.user_key,
            plan_date,
            study_plan_item_id,
            study_session_id,
            _session_progress(payload),
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except (InvalidStudySessionError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post(
    "/api/study-plans/{plan_date}/items/{study_plan_item_id}/sessions/{study_session_id}/complete",
    response_model=ModuleStudySessionResponse,
)
def complete_study_session(
    plan_date: date,
    study_plan_item_id: int,
    study_session_id: int,
    payload: StudySessionProgressRequest,
    learner: Learner,
    services: ApplicationServices = Depends(get_services),
):
    try:
        return services.study_sessions.complete(
            learner.user_key,
            plan_date,
            study_plan_item_id,
            study_session_id,
            _session_progress(payload),
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except (InvalidStudySessionError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.put(
    "/api/study-plans/{plan_date}/items/{study_plan_item_id}",
    response_model=StudyPlanResponse,
)
def override_plan_item(
    plan_date: date,
    study_plan_item_id: int,
    payload: PlanItemOverrideRequest,
    learner: Learner,
    services: ApplicationServices = Depends(get_services),
):
    try:
        services.study_sessions.validate_resource_override(
            learner.user_key,
            plan_date,
            study_plan_item_id,
            payload.resource_id,
        )
        plan = services.adaptation_decisions.override_plan_item(
            learner.user_key,
            plan_date,
            study_plan_item_id,
            planned_minutes=payload.planned_minutes,
            resource_id=payload.resource_id,
            note=payload.note,
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except (InvalidPlanOverrideError, InvalidStudySessionError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return present_plan_response(plan)


@router.patch(
    "/api/study-plans/{plan_date}/items/{study_plan_item_id}/status",
    response_model=StudyPlanResponse,
)
def update_plan_item_status(
    plan_date: date,
    study_plan_item_id: int,
    payload: PlanItemStatusRequest,
    learner: Learner,
    services: ApplicationServices = Depends(get_services),
):
    try:
        plan = services.study_plan.update_item_status(
            learner.user_key,
            plan_date,
            study_plan_item_id,
            payload.status,
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return present_plan_response(plan)


def _session_progress(payload: StudySessionProgressRequest) -> StudySessionProgress:
    return StudySessionProgress(
        active_duration_seconds=payload.active_duration_seconds,
        notes=payload.notes,
        perceived_difficulty=payload.perceived_difficulty,
        confidence=payload.confidence,
    )
