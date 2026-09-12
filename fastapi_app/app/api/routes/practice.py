from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import FASTAPI_ROOT, settings
from app.database import get_db
from app.repositories.sqlalchemy_ielts import SqlAlchemyIeltsPracticeRepository
from app.schemas.ielts import SaveAnswerRequest, SavedAnswerResponse, SubmitAttemptResponse
from app.services.ielts_practice import (
    IeltsPracticeService,
    IncompleteAttemptError,
    PracticeSetNotFoundError,
)


router = APIRouter()
templates = Jinja2Templates(directory=FASTAPI_ROOT / "app" / "templates")
LOCAL_USER_KEY = "local-user"


def get_service(session: Session = Depends(get_db)) -> IeltsPracticeService:
    return IeltsPracticeService(SqlAlchemyIeltsPracticeRepository(session))


@router.get("/")
def home() -> RedirectResponse:
    return RedirectResponse(url="/ielts")


@router.get("/ielts")
def ielts_index(request: Request, service: IeltsPracticeService = Depends(get_service)):
    return templates.TemplateResponse(
        request=request,
        name="ielts/index.html",
        context={"practice_sets": service.list_practice_sets()},
    )


@router.get("/ielts/{slug}")
def practice_workspace(
    slug: str,
    request: Request,
    service: IeltsPracticeService = Depends(get_service),
):
    try:
        workspace = service.get_practice_workspace(slug, LOCAL_USER_KEY)
    except PracticeSetNotFoundError as error:
        raise HTTPException(status_code=404, detail="Practice set not found") from error
    return templates.TemplateResponse(
        request=request,
        name="ielts/practice.html",
        context=workspace,
    )


@router.put("/api/ielts/{slug}/answers/{question_number}", response_model=SavedAnswerResponse)
def save_answer(
    slug: str,
    question_number: int,
    payload: SaveAnswerRequest,
    service: IeltsPracticeService = Depends(get_service),
):
    try:
        return service.save_answer(slug, LOCAL_USER_KEY, question_number, payload.answer)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/api/ielts/{slug}/submit", response_model=SubmitAttemptResponse)
def submit_attempt(slug: str, service: IeltsPracticeService = Depends(get_service)):
    try:
        return service.submit(slug, LOCAL_USER_KEY)
    except IncompleteAttemptError as error:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "请先完成全部题目再提交。",
                "missing_questions": list(error.missing_questions),
            },
        ) from error
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/media/audio/{slug}/{section_number}")
def section_audio(
    slug: str,
    section_number: int,
    service: IeltsPracticeService = Depends(get_service),
):
    try:
        relative_path = service.get_audio_path(slug, section_number)
    except LookupError as error:
        raise HTTPException(status_code=404, detail="Audio not found") from error

    resources_root = settings.resources_root.resolve()
    audio_path = (resources_root / relative_path).resolve()
    if not audio_path.is_relative_to(resources_root) or not audio_path.is_file():
        raise HTTPException(status_code=404, detail="Audio file is unavailable")
    return FileResponse(audio_path, media_type="audio/mpeg", filename=audio_path.name)
