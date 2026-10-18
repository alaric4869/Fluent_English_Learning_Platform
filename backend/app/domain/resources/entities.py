from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum

from app.domain.learning_evidence.entities import Skill


class ResourceSort(StrEnum):
    RECENTLY_ADDED = "recently_added"
    RECENTLY_STUDIED = "recently_studied"
    TITLE = "title"
    PRIORITY = "priority"


class CompletionFilter(StrEnum):
    ALL = "all"
    COMPLETED = "completed"
    NOT_COMPLETED = "not_completed"


@dataclass(frozen=True)
class ResourceLibraryFilters:
    search: str = ""
    skill: Skill | None = None
    resource_type: str = ""
    topic: str = ""
    difficulty: str = ""
    completion: CompletionFilter = CompletionFilter.ALL
    favorite_only: bool = False
    saved_for_later_only: bool = False
    archived_only: bool = False
    sort: ResourceSort = ResourceSort.RECENTLY_ADDED


@dataclass(frozen=True)
class ResourceDraft:
    title: str
    resource_type: str
    skill: Skill
    topic: str
    difficulty: str | None
    estimated_duration_minutes: int
    source_url: str | None = None
    description: str = ""
    content_text: str = ""
    transcript: str = ""
    notes: str = ""
    tags: tuple[str, ...] = ()
    priority: int = 50


@dataclass(frozen=True)
class ResourceStateChanges:
    favorite: bool | None = None
    saved_for_later: bool | None = None
    archived: bool | None = None


@dataclass(frozen=True)
class ResourceCandidate:
    id: int
    slug: str
    title: str
    resource_type: str
    skill: Skill
    topic: str
    difficulty: str | None
    estimated_duration_minutes: int
    priority: int
    tags: tuple[str, ...]
    last_studied_at: datetime | None
    last_assigned_date: date | None
    completed_session_count: int


@dataclass(frozen=True)
class ResourceRecommendation:
    resource_id: int
    score: float
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class LearningResourceDetails:
    id: int
    slug: str
    title: str
    resource_type: str
    skill: Skill
    topic: str
    difficulty: str | None
    estimated_duration_minutes: int
    source_url: str | None
    content: dict
    priority: int
    tags: tuple[str, ...]
    active: bool
    owner_user_key: str | None = None
    description: str = ""
    content_text: str = ""
    transcript: str = ""
    notes: str = ""
    favorite: bool = False
    saved_for_later: bool = False
    archived: bool = False
    last_studied_at: datetime | None = None
    completed_session_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def is_user_owned(self) -> bool:
        return self.owner_user_key is not None


@dataclass(frozen=True)
class ResourceLibrary:
    items: tuple[LearningResourceDetails, ...]
    total_count: int


@dataclass(frozen=True)
class ResourceLibraryFacets:
    resource_types: tuple[str, ...]
    topics: tuple[str, ...]
    difficulties: tuple[str, ...]
