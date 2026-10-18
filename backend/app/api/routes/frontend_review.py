from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.frontend_dependencies import get_frontend_services
from app.api.learner_context import Learner
from app.composition import ApplicationServices
from app.domain.review.entities import (
    ReviewConflictError,
    ReviewQueueItem,
    ReviewTargetType,
)
from app.domain.vocabulary.entities import (
    DuplicateVocabularyError,
    MasteryStatus,
    VocabularyDifficulty,
    VocabularyDraft,
    VocabularyItem,
)
from app.schemas.frontend_review import (
    DueReviewItemResponse,
    ReviewWorkspaceResponse,
    VocabularyLibraryItemResponse,
)
from app.schemas.review import (
    RecordedReviewResponse,
    ReviewRatingRequest,
    VocabularyCreateRequest,
    VocabularyItemResponse,
)
from app.services.vocabulary import InvalidVocabularyError


router = APIRouter(prefix="/api/v1", tags=["frontend-review"])
SYDNEY = ZoneInfo("Australia/Sydney")


@router.get("/review", response_model=ReviewWorkspaceResponse)
def get_review_workspace(
    learner: Learner,
    search: str = "",
    mastery: str = "",
    difficulty: str = "",
    services: ApplicationServices = Depends(get_frontend_services),
) -> ReviewWorkspaceResponse:
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
    source_ids = {
        source_id
        for item in (*library.items, *vocabulary_targets.values(), *sentence_targets.values())
        if (source_id := item.source_resource_id) is not None
    }
    resources = {
        resource_id: resource
        for resource_id in source_ids
        if (resource := services.resources.get_resource(resource_id)) is not None
    }
    due_responses = []
    for item in due_items:
        response = _due_item(item, today, vocabulary_targets, sentence_targets, resources)
        if response is not None:
            due_responses.append(response)
    return ReviewWorkspaceResponse(
        today=today,
        due_count=services.review.get_due_count(learner.user_key, today),
        total_count=library.total_count,
        mastered_count=library.mastered_count,
        due_items=due_responses,
        library_items=[_vocabulary_item(item, resources) for item in library.items],
    )


@router.post(
    "/vocabulary",
    response_model=VocabularyItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_vocabulary_item(
    payload: VocabularyCreateRequest,
    learner: Learner,
    services: ApplicationServices = Depends(get_frontend_services),
) -> VocabularyItemResponse:
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
    return VocabularyItemResponse(
        id=item.id,
        chunk=item.chunk,
        meaning=item.meaning,
        example_sentence=item.example_sentence,
        learned_on=item.learned_on,
        difficulty=item.difficulty,
        mastery_status=item.mastery_status,
        review_item_id=item.review_item_id,
        review_step=item.review_step,
        next_review_date=item.next_review_date,
        review_count=item.review_count,
    )


@router.post(
    "/reviews/{review_item_id}/rate",
    response_model=RecordedReviewResponse,
)
def rate_review_item(
    review_item_id: int,
    payload: ReviewRatingRequest,
    learner: Learner,
    services: ApplicationServices = Depends(get_frontend_services),
) -> RecordedReviewResponse:
    today = datetime.now(SYDNEY).date()
    try:
        result = services.review.record_review(
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
    return RecordedReviewResponse(**result.__dict__)


def _due_item(
    queue_item: ReviewQueueItem,
    today,
    vocabulary_targets,
    sentence_targets,
    resources,
) -> DueReviewItemResponse | None:
    overdue_days = max(0, (today - queue_item.next_review_date).days)
    if queue_item.target_type is ReviewTargetType.VOCABULARY:
        target = vocabulary_targets.get(queue_item.target_id)
        if target is None:
            return None
        title = target.chunk
        secondary_text = target.example_sentence
        answer_label = "MEANING"
        answer = target.meaning
        note = target.personal_note
        target_label = "词块"
    else:
        target = sentence_targets.get(queue_item.target_id)
        if target is None:
            return None
        title = target.sentence
        secondary_text = "先回想这句话在音频中的声音、连读和重音。"
        answer_label = "MEANING / LISTENING NOTE"
        answer = target.meaning or "未填写中文释义"
        note = target.note
        target_label = "听力难句"
    resource = resources.get(target.source_resource_id) if target.source_resource_id else None
    return DueReviewItemResponse(
        review_item_id=queue_item.review_item_id,
        target_type=queue_item.target_type.value,
        target_id=queue_item.target_id,
        title=title,
        secondary_text=secondary_text,
        answer_label=answer_label,
        answer=answer,
        note=note,
        target_label=target_label,
        mastery_status=queue_item.mastery_status.value,
        source_title=resource.title if resource else target.source_context or "手动添加",
        due_label=f"逾期 {overdue_days} 天" if overdue_days else "今天到期",
        next_review_date=queue_item.next_review_date,
        review_count=queue_item.review_count,
    )


def _vocabulary_item(item: VocabularyItem, resources) -> VocabularyLibraryItemResponse:
    resource = resources.get(item.source_resource_id) if item.source_resource_id else None
    return VocabularyLibraryItemResponse(
        id=item.id,
        chunk=item.chunk,
        meaning=item.meaning,
        example_sentence=item.example_sentence,
        learned_on=item.learned_on,
        personal_note=item.personal_note,
        difficulty=item.difficulty.value,
        mastery_status=item.mastery_status.value,
        source_title=resource.title if resource else item.source_context or "手动添加",
        source_context=item.source_context,
        tags=list(item.tags),
        favorite=item.favorite,
        saved_for_later=item.saved_for_later,
        review_item_id=item.review_item_id,
        review_step=item.review_step,
        next_review_date=item.next_review_date,
        last_reviewed_at=item.last_reviewed_at,
        review_count=item.review_count,
    )
