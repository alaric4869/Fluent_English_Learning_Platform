from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.composition import ApplicationServices, build_application_services
from app.config import FASTAPI_ROOT
from app.database import get_db
from app.domain.speaking.entities import RetellingWorkspaceInput
from app.presenters.speaking import (
    present_retelling_record,
    present_sentence_progress,
    present_speaking_workspace,
)
from app.schemas.speaking import (
    SpeakingDraftRequest,
    SpeakingDraftResponse,
    SpeakingSentenceProgressResponse,
    SpeakingSentenceStatusRequest,
    SpeakingSubmissionResponse,
)
from app.services.speaking import IncompleteRetellingError, InvalidRetellingError


router = APIRouter()
templates = Jinja2Templates(directory=FASTAPI_ROOT / "app" / "templates")
LOCAL_USER_KEY = "local-user"


def get_services(session: Session = Depends(get_db)) -> ApplicationServices:
    return build_application_services(session)


@router.get("/speaking/{resource_id}")
def speaking_workspace(
    resource_id: int,
    request: Request,
    services: ApplicationServices = Depends(get_services),
):
    try:
        workspace = services.speaking.get_workspace(LOCAL_USER_KEY, resource_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidRetellingError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return templates.TemplateResponse(
        request=request,
        name="speaking/workspace.html",
        context=present_speaking_workspace(workspace),
    )


@router.put(
    "/api/speaking/{resource_id}/draft",
    response_model=SpeakingDraftResponse,
)
def save_speaking_draft(
    resource_id: int,
    payload: SpeakingDraftRequest,
    services: ApplicationServices = Depends(get_services),
):
    try:
        record = services.speaking.save_workspace_draft(
            LOCAL_USER_KEY,
            resource_id,
            RetellingWorkspaceInput(
                written_outline=payload.written_outline,
                intended_vocabulary=tuple(payload.intended_vocabulary),
                retelling_text=payload.retelling_text,
                mistakes=payload.mistakes,
                improved_version=payload.improved_version,
                practice_status=payload.practice_status,
                active_duration_seconds=payload.active_duration_seconds,
                perceived_difficulty=payload.perceived_difficulty,
                confidence=payload.confidence,
            ),
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidRetellingError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return present_retelling_record(record)


@router.put(
    "/api/speaking/{resource_id}/sentences/{sentence_key}",
    response_model=SpeakingSentenceProgressResponse,
)
def mark_speaking_sentence(
    resource_id: int,
    sentence_key: str,
    payload: SpeakingSentenceStatusRequest,
    services: ApplicationServices = Depends(get_services),
):
    try:
        progress = services.speaking.mark_sentence(
            LOCAL_USER_KEY,
            resource_id,
            sentence_key,
            payload.practice_status,
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidRetellingError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return present_sentence_progress(progress)


@router.post(
    "/api/speaking/{resource_id}/submit",
    response_model=SpeakingSubmissionResponse,
)
def submit_speaking(
    resource_id: int,
    services: ApplicationServices = Depends(get_services),
):
    try:
        record, submission, study_session_id = services.speaking.submit(
            LOCAL_USER_KEY,
            resource_id,
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except IncompleteRetellingError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except InvalidRetellingError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {
        "draft": present_retelling_record(record),
        "submission_id": submission.id,
        "submission_revision": submission.revision,
        "study_session_id": study_session_id,
        "submitted_at": submission.submitted_at,
        "created": submission.created,
    }
