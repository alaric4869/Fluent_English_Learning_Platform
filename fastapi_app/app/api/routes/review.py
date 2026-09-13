from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.composition import ApplicationServices, build_application_services
from app.config import FASTAPI_ROOT
from app.database import get_db
from app.domain.review.entities import ReviewConflictError
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
LOCAL_USER_KEY = "local-user"
SYDNEY = ZoneInfo("Australia/Sydney")


def get_services(session: Session = Depends(get_db)) -> ApplicationServices:
    return build_application_services(session)


@router.get("/review")
def review_page(
    request: Request,
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
    due_items = services.review.get_due_reviews(LOCAL_USER_KEY, today)
    library = services.vocabulary.get_library(
        LOCAL_USER_KEY,
        search=search,
        mastery_status=mastery_filter,
        difficulty=difficulty_filter,
    )
    items = (*due_items, *library.items)
    resources = {
        resource_id: resource
        for item in items
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
            due_count=services.review.get_due_count(LOCAL_USER_KEY, today),
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
    services: ApplicationServices = Depends(get_services),
):
    today = datetime.now(SYDNEY).date()
    try:
        item = services.vocabulary.add_item(
            LOCAL_USER_KEY,
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
    services: ApplicationServices = Depends(get_services),
):
    today = datetime.now(SYDNEY).date()
    try:
        return services.review.record_review(
            LOCAL_USER_KEY,
            review_item_id,
            payload.rating,
            today,
            str(payload.request_id),
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ReviewConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
