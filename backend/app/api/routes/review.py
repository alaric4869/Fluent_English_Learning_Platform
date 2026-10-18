from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.learner_context import Learner
from app.composition import ApplicationServices, build_application_services
from app.config import FASTAPI_ROOT
from app.database import get_db
from app.domain.review.entities import ReviewConflictError
from app.domain.review.entities import ReviewTargetType
from app.domain.vocabulary.entities import (
    DuplicateVocabularyError,
    MasteryStatus,
    VocabularyDifficulty,
    VocabularyDraft,
)
from app.presenters.review import present_review_page, present_vocabulary_response
from app.schemas.review import (
    RecordedReviewResponse,
    ReviewRatingRequest,
    VocabularyCreateRequest,
    VocabularyItemResponse,
)
from app.services.vocabulary import InvalidVocabularyError


router = APIRouter()
templates = Jinja2Templates(directory=FASTAPI_ROOT / "app" / "templates")
SYDNEY = ZoneInfo("Australia/Sydney")


def get_services(session: Session = Depends(get_db)) -> ApplicationServices:
    return build_application_services(session)


@router.get("/review")
def review_page(
    request: Request,
    learner: Learner,
    view: str = "due",
    search: str = "",
    mastery: str = "",
    difficulty: str = "",
    services: ApplicationServices = Depends(get_services),
):
    today = datetime.now(SYDNEY).date()
    try:
        mastery_filter = MasteryStatus(mastery) if mastery else None
        difficulty_filter = VocabularyDifficulty(difficulty) if difficulty else None
    except ValueError as error:
        raise HTTPException(status_code=422, detail="Invalid vocabulary filter") from error
    due_items = services.review.get_due_reviews(learner.user_key, today)
    library = services.vocabulary.get_library(
        learner.user_key,
        search=search,
        mastery_status=mastery_filter,
        difficulty=difficulty_filter,
    )
    vocabulary_targets = {
        item.target_id: target
        for item in due_items
        if item.target_type is ReviewTargetType.VOCABULARY
        if (target := services.vocabulary.get_item(learner.user_key, item.target_id))
        is not None
    }
    sentence_targets = {
        item.target_id: target
        for item in due_items
        if item.target_type is ReviewTargetType.SAVED_SENTENCE
        if (target := services.listening.get_sentence(learner.user_key, item.target_id))
        is not None
    }
    source_items = (*library.items, *vocabulary_targets.values(), *sentence_targets.values())
    resources = {
        resource_id: resource
        for item in source_items
        if item.source_resource_id is not None
        if (resource_id := item.source_resource_id) is not None
        if (resource := services.resources.get_resource(resource_id)) is not None
    }
    return templates.TemplateResponse(
        request=request,
        name="review/index.html",
        context=present_review_page(
            view="library" if view == "library" else "due",
            today=today,
            due_items=due_items,
            vocabulary_targets=vocabulary_targets,
            sentence_targets=sentence_targets,
            due_count=services.review.get_due_count(learner.user_key, today),
            library=library,
            resources=resources,
            search=search,
            mastery_status=mastery_filter,
            difficulty=difficulty_filter,
        ),
    )


@router.post(
    "/api/vocabulary",
    response_model=VocabularyItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_vocabulary_item(
    payload: VocabularyCreateRequest,
    learner: Learner,
    services: ApplicationServices = Depends(get_services),
):
    today = datetime.now(SYDNEY).date()
    try:
        item = services.vocabulary.add_item(
            learner.user_key,
            VocabularyDraft(
                chunk=payload.chunk,
                meaning=payload.meaning,
                example_sentence=payload.example_sentence,
                learned_on=payload.learned_on or today,
                personal_note=payload.personal_note,
                difficulty=payload.difficulty,
                source_resource_id=payload.source_resource_id,
                source_context=payload.source_context,
                tags=tuple(payload.tags),
            ),
            today,
        )
    except DuplicateVocabularyError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except InvalidVocabularyError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return present_vocabulary_response(item)


@router.post(
    "/api/reviews/{review_item_id}/rate",
    response_model=RecordedReviewResponse,
)
def rate_review_item(
    review_item_id: int,
    payload: ReviewRatingRequest,
    learner: Learner,
    services: ApplicationServices = Depends(get_services),
):
    today = datetime.now(SYDNEY).date()
    try:
        return services.review.record_review(
            learner.user_key,
            review_item_id,
            payload.rating,
            today,
            str(payload.request_id),
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ReviewConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
