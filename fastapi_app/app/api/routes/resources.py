from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.composition import ApplicationServices, build_application_services
from app.config import FASTAPI_ROOT
from app.database import get_db
from app.domain.learning_evidence.entities import Skill
from app.domain.resources.entities import (
    CompletionFilter,
    ResourceDraft,
    ResourceLibraryFilters,
    ResourceSort,
    ResourceStateChanges,
)
from app.presenters.resources import (
    present_library_page,
    present_resource_detail,
    present_resource_response,
)
from app.schemas.resources import (
    ResourceResponse,
    ResourceStateRequest,
    ResourceUpsertRequest,
)
from app.services.resources import (
    InvalidResourceError,
    ResourcePermissionError,
)


router = APIRouter()
templates = Jinja2Templates(directory=FASTAPI_ROOT / "app" / "templates")
LOCAL_USER_KEY = "local-user"


def get_services(session: Session = Depends(get_db)) -> ApplicationServices:
    return build_application_services(session)


@router.get("/library")
def library_page(
    request: Request,
    add: bool = False,
    view: str = "all",
    search: str = "",
    skill: str = "",
    resource_type: str = "",
    topic: str = "",
    difficulty: str = "",
    completion: str = "all",
    sort: str = "recently_added",
    services: ApplicationServices = Depends(get_services),
):
    if view not in {"all", "favorites", "saved", "archived"}:
        view = "all"
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
    library = services.resources.get_library(LOCAL_USER_KEY, filters)
    counts = {
        "all": services.resources.get_library(LOCAL_USER_KEY).total_count,
        "favorites": services.resources.get_library(
            LOCAL_USER_KEY, ResourceLibraryFilters(favorite_only=True)
        ).total_count,
        "saved": services.resources.get_library(
            LOCAL_USER_KEY, ResourceLibraryFilters(saved_for_later_only=True)
        ).total_count,
        "archived": services.resources.get_library(
            LOCAL_USER_KEY, ResourceLibraryFilters(archived_only=True)
        ).total_count,
    }
    return templates.TemplateResponse(
        request=request,
        name="resources/index.html",
        context=present_library_page(
            library=library,
            facets=services.resources.get_library_facets(LOCAL_USER_KEY),
            filters=filters,
            view=view,
            counts=counts,
            open_add_resource=add,
        ),
    )


@router.get("/library/{resource_id}")
def resource_detail_page(
    resource_id: int,
    request: Request,
    services: ApplicationServices = Depends(get_services),
):
    resource = services.resources.get_user_resource(LOCAL_USER_KEY, resource_id)
    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    return templates.TemplateResponse(
        request=request,
        name="resources/detail.html",
        context=present_resource_detail(resource),
    )


@router.post(
    "/api/resources",
    response_model=ResourceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_resource(
    payload: ResourceUpsertRequest,
    services: ApplicationServices = Depends(get_services),
):
    try:
        resource = services.resources.add_resource(
            LOCAL_USER_KEY, _draft(payload)
        )
    except InvalidResourceError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return present_resource_response(resource)


@router.put("/api/resources/{resource_id}", response_model=ResourceResponse)
def update_resource(
    resource_id: int,
    payload: ResourceUpsertRequest,
    services: ApplicationServices = Depends(get_services),
):
    try:
        resource = services.resources.update_resource(
            LOCAL_USER_KEY, resource_id, _draft(payload)
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ResourcePermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except InvalidResourceError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return present_resource_response(resource)


@router.patch("/api/resources/{resource_id}/state", response_model=ResourceResponse)
def update_resource_state(
    resource_id: int,
    payload: ResourceStateRequest,
    services: ApplicationServices = Depends(get_services),
):
    try:
        resource = services.resources.update_user_state(
            LOCAL_USER_KEY,
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
    return present_resource_response(resource)


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
