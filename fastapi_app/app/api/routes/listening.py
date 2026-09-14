from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.composition import ApplicationServices, build_application_services
from app.config import FASTAPI_ROOT
from app.database import get_db
from app.presenters.listening import present_listening_workspace
from app.schemas.listening import TranscriptSentenceMarkRequest
from app.schemas.notebook import ListeningSentenceResponse
from app.services.listening import InvalidListeningSentenceError


router = APIRouter()
templates = Jinja2Templates(directory=FASTAPI_ROOT / "app" / "templates")
LOCAL_USER_KEY = "local-user"
SYDNEY = ZoneInfo("Australia/Sydney")


def get_services(session: Session = Depends(get_db)) -> ApplicationServices:
    return build_application_services(session)


@router.get("/listening/{resource_id}")
def listening_workspace(
    resource_id: int,
    request: Request,
    services: ApplicationServices = Depends(get_services),
):
    resource = services.resources.get_user_resource(LOCAL_USER_KEY, resource_id)
    if resource is None:
        raise HTTPException(status_code=404, detail="Listening resource not found")
    try:
        saved = services.listening.list_for_resource(LOCAL_USER_KEY, resource_id)
    except InvalidListeningSentenceError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return templates.TemplateResponse(
        request=request,
        name="listening/workspace.html",
        context=present_listening_workspace(resource, saved),
    )


@router.post(
    "/api/listening/resources/{resource_id}/sentences",
    response_model=ListeningSentenceResponse,
)
def mark_transcript_sentence(
    resource_id: int,
    payload: TranscriptSentenceMarkRequest,
    services: ApplicationServices = Depends(get_services),
):
    try:
        item = services.listening.mark_transcript_sentence(
            LOCAL_USER_KEY,
            resource_id,
            payload.sentence,
            payload.practice_status,
            datetime.now(SYDNEY).date(),
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidListeningSentenceError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {
        "id": item.id,
        "sentence": item.sentence,
        "meaning": item.meaning,
        "learned_on": item.learned_on,
        "practice_status": item.practice_status,
        "note": item.note,
        "source_context": item.source_context,
        "review_item_id": item.review_item_id,
        "next_review_date": item.next_review_date,
        "review_count": item.review_count,
        "mastery_status": item.mastery_status,
    }
