from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.composition import ApplicationServices, build_application_services
from app.config import FASTAPI_ROOT
from app.database import get_db
from app.presenters.dashboard import present_dashboard
from app.presenters.weekly_review import present_weekly_review


router = APIRouter()
templates = Jinja2Templates(directory=FASTAPI_ROOT / "app" / "templates")
LOCAL_USER_KEY = "local-user"
SYDNEY = ZoneInfo("Australia/Sydney")


def get_services(session: Session = Depends(get_db)) -> ApplicationServices:
    return build_application_services(session)


@router.get("/dashboard")
def dashboard_page(
    request: Request,
    services: ApplicationServices = Depends(get_services),
):
    now = datetime.now(SYDNEY)
    snapshot = services.dashboard.get_snapshot(LOCAL_USER_KEY, now.date())
    resources = {
        item.resource_id: resource
        for item in snapshot.today_plan.items
        if item.resource_id is not None
        if (resource := services.resources.get_resource(item.resource_id)) is not None
    }
    return templates.TemplateResponse(
        request=request,
        name="dashboard/index.html",
        context=present_dashboard(snapshot, now, resources),
    )


@router.get("/weekly-review")
def weekly_review_page(
    request: Request,
    services: ApplicationServices = Depends(get_services),
):
    today = datetime.now(SYDNEY).date()
    review = services.weekly_review.get_current_week(LOCAL_USER_KEY, today)
    return templates.TemplateResponse(
        request=request,
        name="weekly_review/index.html",
        context=present_weekly_review(review),
    )
