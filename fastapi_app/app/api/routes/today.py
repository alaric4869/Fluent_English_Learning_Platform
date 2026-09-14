from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.composition import ApplicationServices, build_application_services
from app.config import FASTAPI_ROOT
from app.database import get_db
from app.domain.learning_evidence.entities import Skill
from app.domain.study_session.entities import StudySessionProgress
from app.presenters.today import present_plan_response, present_today_plan
from app.schemas.study_plan import (
    PlanItemOverrideRequest,
    PlanItemStatusRequest,
    StudyPlanResponse,
)
from app.schemas.study_session import (
    ModuleStudySessionResponse,
    StudySessionProgressRequest,
)
from app.services.adaptive_learning import InvalidPlanOverrideError
from app.services.study_session import InvalidStudySessionError


router = APIRouter()
templates = Jinja2Templates(directory=FASTAPI_ROOT / "app" / "templates")
LOCAL_USER_KEY = "local-user"
SYDNEY = ZoneInfo("Australia/Sydney")


def get_services(session: Session = Depends(get_db)) -> ApplicationServices:
    return build_application_services(session)


@router.get("/today")
def today_page(
    request: Request,
    services: ApplicationServices = Depends(get_services),
):
    now = datetime.now(SYDNEY)
    plan = services.study_plan.get_or_create_daily_plan(LOCAL_USER_KEY, now.date())
    resources = {
        item.resource_id: services.resources.get_resource(item.resource_id)
        for item in plan.items
        if item.resource_id is not None
    }
    resource_options = {
        skill: services.resources.list_available_for_skill(
            LOCAL_USER_KEY,
            skill,
            plan.plan_date,
        )
        for skill in Skill
    }
    return templates.TemplateResponse(
        request=request,
        name="today/index.html",
        context=present_today_plan(
            plan,
            now,
            resources,
            resource_options,
            services.review.get_due_count(LOCAL_USER_KEY, now.date()),
            services.study_sessions.get_latest_for_plan(
                LOCAL_USER_KEY, plan.plan_date
            ),
        ),
    )


@router.post(
    "/api/study-plans/{plan_date}/items/{study_plan_item_id}/sessions",
    response_model=ModuleStudySessionResponse,
)
def start_study_session(
    plan_date: date,
    study_plan_item_id: int,
    services: ApplicationServices = Depends(get_services),
):
    try:
        return services.study_sessions.start(
            LOCAL_USER_KEY, plan_date, study_plan_item_id
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
    services: ApplicationServices = Depends(get_services),
):
    try:
        return services.study_sessions.save_progress(
            LOCAL_USER_KEY,
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
    services: ApplicationServices = Depends(get_services),
):
    try:
        return services.study_sessions.complete(
            LOCAL_USER_KEY,
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
    services: ApplicationServices = Depends(get_services),
):
    try:
        services.study_sessions.validate_resource_override(
            LOCAL_USER_KEY,
            plan_date,
            study_plan_item_id,
            payload.resource_id,
        )
        plan = services.adaptation_decisions.override_plan_item(
            LOCAL_USER_KEY,
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
    services: ApplicationServices = Depends(get_services),
):
    try:
        plan = services.study_plan.update_item_status(
            LOCAL_USER_KEY,
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
