from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.composition import ApplicationServices, build_application_services
from app.config import FASTAPI_ROOT, settings
from app.database import get_db
from app.api.learner_context import Learner
from app.domain.learning_evidence.entities import Skill
from app.domain.resources.entities import ResourceLibraryFilters, ResourceSort
from app.presenters.ielts import present_practice_workspace
from app.schemas.ielts import SaveAnswerRequest, SavedAnswerResponse, SubmitAttemptResponse
from app.services.ielts_practice import (
    IeltsPracticeService,
    IncompleteAttemptError,
    PracticeSetNotFoundError,
)


router = APIRouter()
templates = Jinja2Templates(directory=FASTAPI_ROOT / "app" / "templates")


def get_service(session: Session = Depends(get_db)) -> IeltsPracticeService:
    return build_application_services(session).ielts_practice


def get_services(session: Session = Depends(get_db)) -> ApplicationServices:
    return build_application_services(session)


@router.get("/")
def home() -> RedirectResponse:
    return RedirectResponse(url="/dashboard")


@router.get("/ielts")
def ielts_index(
    request: Request,
    learner: Learner,
    services: ApplicationServices = Depends(get_services),
):
    return templates.TemplateResponse(
        request=request,
        name="ielts/index.html",
        context={
            "practice_sets": services.ielts_practice.list_practice_sets(),
            "speaking_resources": services.resources.get_library(
                learner.user_key,
                ResourceLibraryFilters(
                    skill=Skill.SPEAKING,
                    resource_type="shadowing_retelling",
                    sort=ResourceSort.PRIORITY,
                ),
            ).items,
            "writing_resources": services.resources.get_library(
                learner.user_key,
                ResourceLibraryFilters(
                    skill=Skill.WRITING,
                    resource_type="ielts_writing",
                    sort=ResourceSort.PRIORITY,
                ),
            ).items,
        },
    )


@router.get("/ielts/{slug}")
def practice_workspace(
    slug: str,
    request: Request,
    learner: Learner,
    service: IeltsPracticeService = Depends(get_service),
):
    try:
        workspace = service.get_practice_workspace(slug, learner.user_key)
    except PracticeSetNotFoundError as error:
        raise HTTPException(status_code=404, detail="Practice set not found") from error
    return templates.TemplateResponse(
        request=request,
        name="ielts/practice.html",
        context=present_practice_workspace(workspace),
    )


@router.put("/api/ielts/{slug}/answers/{question_number}", response_model=SavedAnswerResponse)
def save_answer(
    slug: str,
    question_number: int,
    payload: SaveAnswerRequest,
    learner: Learner,
    service: IeltsPracticeService = Depends(get_service),
):
    try:
        return service.save_answer(slug, learner.user_key, question_number, payload.answer)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/api/ielts/{slug}/submit", response_model=SubmitAttemptResponse)
def submit_attempt(
    slug: str,
    learner: Learner,
    service: IeltsPracticeService = Depends(get_service),
):
    try:
        return service.submit(slug, learner.user_key)
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


@router.get("/media/ielts-assets/{asset_path:path}")
def ielts_question_asset(asset_path: str):
    assets_root = settings.ielts_assets_root.resolve()
    resolved_asset = (assets_root / Path(asset_path)).resolve()
    if not resolved_asset.is_relative_to(assets_root) or not resolved_asset.is_file():
        raise HTTPException(status_code=404, detail="Question asset is unavailable")
    return FileResponse(resolved_asset)
