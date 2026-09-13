from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import FASTAPI_ROOT, settings
from app.database import get_db
from app.domain.learner_profile.rule_based_evaluator import RuleBasedSkillEvaluator
from app.presenters.ielts import present_practice_workspace
from app.repositories.sqlalchemy_ielts import SqlAlchemyIeltsPracticeRepository
from app.repositories.sqlalchemy_learning_evidence import SqlAlchemyLearningEvidenceRepository
from app.repositories.sqlalchemy_learner_profile import SqlAlchemyLearnerProfileRepository
from app.schemas.ielts import SaveAnswerRequest, SavedAnswerResponse, SubmitAttemptResponse
from app.services.ielts_practice import (
    IeltsPracticeService,
    IncompleteAttemptError,
    PracticeSetNotFoundError,
)
from app.services.ielts_learning_evidence import IeltsLearningEvidenceRecorder
from app.services.learning_evidence import LearningEvidenceService
from app.services.learner_profile import LearnerProfileService


router = APIRouter()
templates = Jinja2Templates(directory=FASTAPI_ROOT / "app" / "templates")
LOCAL_USER_KEY = "local-user"


def get_service(session: Session = Depends(get_db)) -> IeltsPracticeService:
    evidence_service = LearningEvidenceService(SqlAlchemyLearningEvidenceRepository(session))
    profile_service = LearnerProfileService(
        evidence_service,
        SqlAlchemyLearnerProfileRepository(session),
        RuleBasedSkillEvaluator(),
    )
    evidence_recorder = IeltsLearningEvidenceRecorder(evidence_service, profile_service)
    return IeltsPracticeService(
        SqlAlchemyIeltsPracticeRepository(session),
        submission_observer=evidence_recorder,
    )


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
        context=present_practice_workspace(workspace),
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


@router.get("/media/ielts-assets/{asset_path:path}")
def ielts_question_asset(asset_path: str):
    assets_root = settings.ielts_assets_root.resolve()
    resolved_asset = (assets_root / Path(asset_path)).resolve()
    if not resolved_asset.is_relative_to(assets_root) or not resolved_asset.is_file():
        raise HTTPException(status_code=404, detail="Question asset is unavailable")
    return FileResponse(resolved_asset)
