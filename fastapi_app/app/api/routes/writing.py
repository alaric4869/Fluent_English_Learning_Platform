from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.composition import ApplicationServices, build_application_services
from app.config import FASTAPI_ROOT
from app.database import get_db
from app.domain.ai_evaluation.mock_evaluator import WorkEvaluatorUnavailableError
from app.domain.writing.entities import WritingDraftInput
from app.presenters.ai_evaluation import present_work_evaluation
from app.presenters.writing import present_writing_draft, present_writing_workspace
from app.schemas.ai_evaluation import WorkEvaluationResponse
from app.schemas.writing import (
    WritingDraftRequest,
    WritingDraftResponse,
    WritingSubmissionResponse,
)
from app.services.writing import (
    IncompleteWritingDraftError,
    InvalidWritingDraftError,
)
from app.services.ai_evaluation import InvalidEvaluationSourceError


router = APIRouter()
templates = Jinja2Templates(directory=FASTAPI_ROOT / "app" / "templates")
LOCAL_USER_KEY = "local-user"


def get_services(session: Session = Depends(get_db)) -> ApplicationServices:
    return build_application_services(session)


@router.get("/writing/{resource_id}")
def writing_workspace(
    resource_id: int,
    request: Request,
    services: ApplicationServices = Depends(get_services),
):
    try:
        workspace = services.writing.get_workspace(LOCAL_USER_KEY, resource_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidWritingDraftError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return templates.TemplateResponse(
        request=request,
        name="writing/workspace.html",
        context=present_writing_workspace(
            workspace,
            evaluation=services.ai_evaluation.get_latest_writing_evaluation(
                LOCAL_USER_KEY,
                resource_id,
            ),
            evaluation_available=services.ai_evaluation.available,
        ),
    )


@router.put(
    "/api/writing/{resource_id}/draft",
    response_model=WritingDraftResponse,
)
def save_writing_draft(
    resource_id: int,
    payload: WritingDraftRequest,
    services: ApplicationServices = Depends(get_services),
):
    try:
        draft = services.writing.save_draft(
            LOCAL_USER_KEY,
            resource_id,
            WritingDraftInput(**payload.model_dump()),
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidWritingDraftError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return present_writing_draft(draft)


@router.post(
    "/api/writing/{resource_id}/submit",
    response_model=WritingSubmissionResponse,
)
def submit_writing(
    resource_id: int,
    services: ApplicationServices = Depends(get_services),
):
    try:
        draft, submission, study_session_id = services.writing.submit(
            LOCAL_USER_KEY,
            resource_id,
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except IncompleteWritingDraftError as error:
        raise HTTPException(
            status_code=422,
            detail={
                "message": str(error),
                "word_count": error.word_count,
                "minimum_words": error.minimum_words,
            },
        ) from error
    except InvalidWritingDraftError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {
        "draft": present_writing_draft(draft),
        "submission_id": submission.id,
        "submission_revision": submission.revision,
        "study_session_id": study_session_id,
        "word_count": submission.word_count,
        "submitted_at": submission.submitted_at,
        "created": submission.created,
    }


@router.post(
    "/api/writing/{resource_id}/evaluation",
    response_model=WorkEvaluationResponse,
)
def evaluate_writing(
    resource_id: int,
    services: ApplicationServices = Depends(get_services),
):
    try:
        evaluation = services.ai_evaluation.evaluate_writing(
            LOCAL_USER_KEY,
            resource_id,
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidEvaluationSourceError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except WorkEvaluatorUnavailableError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return present_work_evaluation(evaluation)
