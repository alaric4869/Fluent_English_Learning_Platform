from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.frontend_dependencies import get_frontend_services
from app.api.learner_context import Learner
from app.composition import ApplicationServices
from app.domain.learning_evidence.entities import Skill
from app.domain.resources.entities import (
    CompletionFilter,
    LearningResourceDetails,
    ResourceDraft,
    ResourceLibraryFilters,
    ResourceSort,
    ResourceStateChanges,
)
from app.schemas.frontend_resources import (
    ResourceCountsResponse,
    ResourceDetailResponse,
    ResourceFacetsResponse,
    ResourceLibraryResponse,
    ResourceSummaryResponse,
)
from app.schemas.resources import ResourceStateRequest, ResourceUpsertRequest
from app.services.resources import InvalidResourceError, ResourcePermissionError


router = APIRouter(prefix="/api/v1/library", tags=["frontend-library"])


@router.get("", response_model=ResourceLibraryResponse)
def get_library(
    learner: Learner,
    view: str = "all",
    search: str = "",
    skill: str = "",
    resource_type: str = "",
    topic: str = "",
    difficulty: str = "",
    completion: str = "all",
    sort: str = "recently_added",
    services: ApplicationServices = Depends(get_frontend_services),
) -> ResourceLibraryResponse:
    if view not in {"all", "favorites", "saved", "archived"}:
        raise HTTPException(status_code=422, detail="Invalid library view")
    try:
        selected_skill = Skill(skill) if skill else None
        selected_completion = CompletionFilter(completion)
        selected_sort = ResourceSort(sort)
    except ValueError as error:
        raise HTTPException(status_code=422, detail="Invalid resource filter") from error
    filters = ResourceLibraryFilters(
        search=search.strip(),
        skill=selected_skill,
        resource_type=resource_type,
        topic=topic,
        difficulty=difficulty,
        completion=selected_completion,
        favorite_only=view == "favorites",
        saved_for_later_only=view == "saved",
        archived_only=view == "archived",
        sort=selected_sort,
    )
    library = services.resources.get_library(learner.user_key, filters)
    facets = services.resources.get_library_facets(learner.user_key)
    counts = ResourceCountsResponse(
        all=services.resources.get_library(learner.user_key).total_count,
        favorites=services.resources.get_library(
            learner.user_key, ResourceLibraryFilters(favorite_only=True)
        ).total_count,
        saved=services.resources.get_library(
            learner.user_key, ResourceLibraryFilters(saved_for_later_only=True)
        ).total_count,
        archived=services.resources.get_library(
            learner.user_key, ResourceLibraryFilters(archived_only=True)
        ).total_count,
    )
    return ResourceLibraryResponse(
        view=view,
        total_count=library.total_count,
        counts=counts,
        facets=ResourceFacetsResponse(
            resource_types=list(facets.resource_types),
            topics=list(facets.topics),
            difficulties=list(facets.difficulties),
        ),
        items=[_summary(item) for item in library.items],
    )


@router.get("/{resource_id}", response_model=ResourceDetailResponse)
def get_resource(
    resource_id: int,
    learner: Learner,
    services: ApplicationServices = Depends(get_frontend_services),
) -> ResourceDetailResponse:
    resource = services.resources.get_user_resource(learner.user_key, resource_id)
    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    return _detail(resource)


@router.post(
    "",
    response_model=ResourceDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_resource(
    payload: ResourceUpsertRequest,
    learner: Learner,
    services: ApplicationServices = Depends(get_frontend_services),
) -> ResourceDetailResponse:
    try:
        resource = services.resources.add_resource(learner.user_key, _draft(payload))
    except InvalidResourceError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return _detail(resource)


@router.put("/{resource_id}", response_model=ResourceDetailResponse)
def update_resource(
    resource_id: int,
    payload: ResourceUpsertRequest,
    learner: Learner,
    services: ApplicationServices = Depends(get_frontend_services),
) -> ResourceDetailResponse:
    try:
        resource = services.resources.update_resource(
            learner.user_key, resource_id, _draft(payload)
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ResourcePermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except InvalidResourceError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return _detail(resource)


@router.patch("/{resource_id}/state", response_model=ResourceDetailResponse)
def update_resource_state(
    resource_id: int,
    payload: ResourceStateRequest,
    learner: Learner,
    services: ApplicationServices = Depends(get_frontend_services),
) -> ResourceDetailResponse:
    try:
        resource = services.resources.update_user_state(
            learner.user_key,
            resource_id,
            ResourceStateChanges(
                favorite=payload.favorite,
                saved_for_later=payload.saved_for_later,
                archived=payload.archived,
            ),
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidResourceError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return _detail(resource)


def _draft(payload: ResourceUpsertRequest) -> ResourceDraft:
    return ResourceDraft(
        title=payload.title,
        resource_type=payload.resource_type,
        skill=payload.skill,
        topic=payload.topic,
        difficulty=payload.difficulty,
        estimated_duration_minutes=payload.estimated_duration_minutes,
        source_url=payload.source_url,
        description=payload.description,
        content_text=payload.content_text,
        transcript=payload.transcript,
        notes=payload.notes,
        tags=tuple(payload.tags),
        priority=payload.priority,
    )


def _summary(resource: LearningResourceDetails) -> ResourceSummaryResponse:
    return ResourceSummaryResponse(
        id=resource.id,
        title=resource.title,
        resource_type=resource.resource_type,
        skill=resource.skill.value,
        topic=resource.topic,
        difficulty=resource.difficulty,
        estimated_duration_minutes=resource.estimated_duration_minutes,
        source_url=resource.source_url,
        description=resource.description,
        tags=list(resource.tags),
        priority=resource.priority,
        favorite=resource.favorite,
        saved_for_later=resource.saved_for_later,
        archived=resource.archived,
        is_user_owned=resource.is_user_owned,
        last_studied_at=resource.last_studied_at,
        completed_session_count=resource.completed_session_count,
        start_href=_start_href(resource),
    )


def _detail(resource: LearningResourceDetails) -> ResourceDetailResponse:
    return ResourceDetailResponse(
        **_summary(resource).model_dump(),
        content_text=resource.content_text,
        transcript=resource.transcript,
        notes=resource.notes,
    )


def _start_href(resource: LearningResourceDetails) -> str | None:
    if resource.skill in {Skill.LISTENING, Skill.SPEAKING, Skill.WRITING}:
        return f"/{resource.skill.value}/{resource.id}"
    practice_slug = resource.content.get("practice_set_slug")
    if isinstance(practice_slug, str) and practice_slug:
        return f"/ielts/{practice_slug}"
    if resource.source_url and urlparse(resource.source_url).scheme in {"http", "https"}:
        return resource.source_url
    return None
