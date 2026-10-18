from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.learner_context import Learner
from app.composition import ApplicationServices, build_application_services
from app.config import FASTAPI_ROOT
from app.database import get_db
from app.presenters.dashboard import present_dashboard
from app.presenters.agent_coaching import (
    present_weekly_coaching_report,
    present_weekly_coaching_response,
)
from app.presenters.weekly_review import present_weekly_review
from app.schemas.agent_coaching import WeeklyCoachingResponse
from app.services.agent_coaching import (
    AgentCoachingGenerationError,
    AgentCoachingUnavailableError,
)


router = APIRouter()
templates = Jinja2Templates(directory=FASTAPI_ROOT / "app" / "templates")
SYDNEY = ZoneInfo("Australia/Sydney")


def get_services(session: Session = Depends(get_db)) -> ApplicationServices:
    return build_application_services(session)


@router.get("/dashboard")
def dashboard_page(
    request: Request,
    learner: Learner,
    services: ApplicationServices = Depends(get_services),
):
    now = datetime.now(SYDNEY)
    snapshot = services.dashboard.get_snapshot(learner.user_key, now.date())
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
    learner: Learner,
    services: ApplicationServices = Depends(get_services),
):
    today = datetime.now(SYDNEY).date()
    review = services.weekly_review.get_current_week(learner.user_key, today)
    context = present_weekly_review(review)
    context.update(
        {
            "agent_available": services.agent_coaching.available,
            "agent_unavailable_reason": services.agent_coaching.unavailable_reason,
            "agent_report": present_weekly_coaching_report(
                services.agent_coaching.get_latest(learner.user_key, today)
            ),
        }
    )
    return templates.TemplateResponse(
        request=request,
        name="weekly_review/index.html",
        context=context,
    )


@router.post(
    "/api/agent/weekly-coaching",
    response_model=WeeklyCoachingResponse,
)
def generate_weekly_coaching(
    learner: Learner,
    services: ApplicationServices = Depends(get_services),
):
    today = datetime.now(SYDNEY).date()
    try:
        report = services.agent_coaching.generate(learner.user_key, today)
    except AgentCoachingUnavailableError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except AgentCoachingGenerationError as error:
        raise HTTPException(
            status_code=502,
            detail="AI 服务暂时无法生成周报，请稍后重试。",
        ) from error
    return present_weekly_coaching_response(report)
