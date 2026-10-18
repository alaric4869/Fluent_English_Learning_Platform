from datetime import datetime

from pydantic import BaseModel


class ResourceSummaryResponse(BaseModel):
    id: int
    title: str
    resource_type: str
    skill: str
    topic: str
    difficulty: str | None
    estimated_duration_minutes: int
    source_url: str | None
    description: str
    tags: list[str]
    priority: int
    favorite: bool
    saved_for_later: bool
    archived: bool
    is_user_owned: bool
    last_studied_at: datetime | None
    completed_session_count: int
    start_href: str | None


class ResourceDetailResponse(ResourceSummaryResponse):
    content_text: str
    transcript: str
    notes: str


class ResourceFacetsResponse(BaseModel):
    resource_types: list[str]
    topics: list[str]
    difficulties: list[str]


class ResourceCountsResponse(BaseModel):
    all: int
    favorites: int
    saved: int
    archived: int


class ResourceLibraryResponse(BaseModel):
    view: str
    total_count: int
    counts: ResourceCountsResponse
    facets: ResourceFacetsResponse
    items: list[ResourceSummaryResponse]
