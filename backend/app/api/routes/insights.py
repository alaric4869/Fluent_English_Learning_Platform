from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.learner_context import Learner
from app.composition import ApplicationServices, build_application_services
from app.config import FASTAPI_ROOT
from app.database import get_db
from app.presenters.history import present_history_detail, present_history_index
from app.presenters.progress import present_progress


router = APIRouter()
templates = Jinja2Templates(directory=FASTAPI_ROOT / "app" / "templates")
SYDNEY = ZoneInfo("Australia/Sydney")


def get_services(session: Session = Depends(get_db)) -> ApplicationServices:
    return build_application_services(session)


@router.get("/history")
def history_page(
    request: Request,
    learner: Learner,
    view: str = "timeline",
    month: str | None = None,
    services: ApplicationServices = Depends(get_services),
):
    today = datetime.now(SYDNEY).date()
    selected_month = _parse_month(month, today)
    history = (
        services.history.list_month(learner.user_key, selected_month)
        if view == "calendar"
        else services.history.list_recent_days(learner.user_key, today)
    )
    resources = _load_plan_resources(history, services)
    return templates.TemplateResponse(
        request=request,
        name="history/index.html",
        context=present_history_index(
            history,
            today,
            selected_month,
            "calendar" if view == "calendar" else "timeline",
            resources,
        ),
    )


@router.get("/history/{study_date}")
def history_detail_page(
    study_date: date,
    request: Request,
    learner: Learner,
    services: ApplicationServices = Depends(get_services),
):
    history_day = services.history.get_day(learner.user_key, study_date)
    if history_day is None:
        raise HTTPException(status_code=404, detail="Study history not found")
    resources = _load_plan_resources((history_day,), services)
    return templates.TemplateResponse(
        request=request,
        name="history/detail.html",
        context=present_history_detail(history_day, resources),
    )


@router.get("/progress")
def progress_page(
    request: Request,
    learner: Learner,
    services: ApplicationServices = Depends(get_services),
):
    today = datetime.now(SYDNEY).date()
    summary = services.progress_analytics.get_summary(learner.user_key, today)
    return templates.TemplateResponse(
        request=request,
        name="progress/index.html",
        context=present_progress(summary),
    )


def _load_plan_resources(history, services: ApplicationServices):
    resource_ids = {
        item.resource_id
        for day in history
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
