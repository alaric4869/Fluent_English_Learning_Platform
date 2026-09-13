from datetime import date
from typing import Protocol

from app.domain.learning_evidence.entities import Skill
from app.domain.resources.entities import (
    LearningResourceDetails,
    ResourceCandidate,
    ResourceDraft,
    ResourceLibraryFacets,
    ResourceLibraryFilters,
    ResourceStateChanges,
)


class ResourceRepository(Protocol):
    def list_candidates(
        self,
        user_key: str,
        skill: Skill,
        target_date: date,
    ) -> tuple[ResourceCandidate, ...]: ...

    def get(self, resource_id: int) -> LearningResourceDetails | None: ...

    def get_for_user(
        self, user_key: str, resource_id: int
    ) -> LearningResourceDetails | None: ...

    def list_library(
        self,
        user_key: str,
        filters: ResourceLibraryFilters,
        limit: int,
    ) -> tuple[LearningResourceDetails, ...]: ...

    def count_library(self, user_key: str, filters: ResourceLibraryFilters) -> int: ...

    def get_facets(self, user_key: str) -> ResourceLibraryFacets: ...

    def create(
        self,
        user_key: str,
        slug: str,
        draft: ResourceDraft,
    ) -> LearningResourceDetails: ...

    def update(
        self,
        user_key: str,
        resource_id: int,
        draft: ResourceDraft,
    ) -> LearningResourceDetails | None: ...

    def set_user_state(
        self,
        user_key: str,
        resource_id: int,
        changes: ResourceStateChanges,
    ) -> LearningResourceDetails | None: ...
