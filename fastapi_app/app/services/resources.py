from datetime import date
from urllib.parse import urlparse
from uuid import uuid4

from app.domain.learning_evidence.entities import Skill
from app.domain.resources.entities import (
    LearningResourceDetails,
    ResourceCandidate,
    ResourceDraft,
    ResourceLibrary,
    ResourceLibraryFacets,
    ResourceLibraryFilters,
    ResourceRecommendation,
    ResourceStateChanges,
)
from app.domain.resources.recommender import ResourceRecommender
from app.domain.resources.repository import ResourceRepository
from app.domain.weakness_detection.entities import SkillClassification


class ResourceService:
    def __init__(
        self,
        repository: ResourceRepository,
        recommender: ResourceRecommender,
    ) -> None:
        self.repository = repository
        self.recommender = recommender

    @property
    def recommender_version(self) -> str:
        return self.recommender.recommender_version

    def recommend_for_skill(
        self,
        user_key: str,
        skill: Skill,
        classification: SkillClassification,
        target_date: date,
    ) -> ResourceRecommendation | None:
        recommendations = self.recommend_resources(
            user_key,
            skill,
            classification,
            target_date,
            count=1,
        )
        return recommendations[0] if recommendations else None

    def recommend_resources(
        self,
        user_key: str,
        skill: Skill,
        classification: SkillClassification,
        target_date: date,
        *,
        count: int = 3,
        difficulty: str | None = None,
    ) -> tuple[ResourceRecommendation, ...]:
        if count < 1 or count > 20:
            raise ValueError("count must be between 1 and 20")
        candidates = self.repository.list_candidates(user_key, skill, target_date)
        if difficulty:
            normalized_difficulty = difficulty.casefold().strip()
            candidates = tuple(
                candidate
                for candidate in candidates
                if (candidate.difficulty or "").casefold() == normalized_difficulty
            )
        return self.recommender.recommend(
            skill,
            classification,
            candidates,
            target_date,
            count=count,
        )

    def get_resource(self, resource_id: int) -> LearningResourceDetails | None:
        return self.repository.get(resource_id)

    def list_available_for_skill(
        self,
        user_key: str,
        skill: Skill,
        target_date: date,
    ) -> tuple[ResourceCandidate, ...]:
        return self.repository.list_candidates(user_key, skill, target_date)

    def get_user_resource(
        self,
        user_key: str,
        resource_id: int,
    ) -> LearningResourceDetails | None:
        return self.repository.get_for_user(user_key, resource_id)

    def get_library(
        self,
        user_key: str,
        filters: ResourceLibraryFilters | None = None,
        limit: int = 200,
    ) -> ResourceLibrary:
        if limit < 1 or limit > 500:
            raise ValueError("limit must be between 1 and 500")
        selected = filters or ResourceLibraryFilters()
        return ResourceLibrary(
            items=self.repository.list_library(user_key, selected, limit),
            total_count=self.repository.count_library(user_key, selected),
        )

    def get_library_facets(self, user_key: str) -> ResourceLibraryFacets:
        return self.repository.get_facets(user_key)

    def add_resource(
        self,
        user_key: str,
        draft: ResourceDraft,
    ) -> LearningResourceDetails:
        normalized = _normalize_draft(draft)
        return self.repository.create(
            user_key,
            f"personal-{uuid4().hex}",
            normalized,
        )

    def update_resource(
        self,
        user_key: str,
        resource_id: int,
        draft: ResourceDraft,
    ) -> LearningResourceDetails:
        existing = self.repository.get_for_user(user_key, resource_id)
        if existing is None:
            raise LookupError("Resource not found")
        if existing.owner_user_key != user_key:
            raise ResourcePermissionError("Built-in resources cannot be edited")
        updated = self.repository.update(user_key, resource_id, _normalize_draft(draft))
        if updated is None:
            raise LookupError("Resource not found")
        return updated

    def update_user_state(
        self,
        user_key: str,
        resource_id: int,
        changes: ResourceStateChanges,
    ) -> LearningResourceDetails:
        if all(
            value is None
            for value in (
                changes.favorite,
                changes.saved_for_later,
                changes.archived,
            )
        ):
            raise InvalidResourceError("At least one resource state is required")
        updated = self.repository.set_user_state(user_key, resource_id, changes)
        if updated is None:
            raise LookupError("Resource not found")
        return updated


class InvalidResourceError(ValueError):
    pass


class ResourcePermissionError(PermissionError):
    pass


def _normalize_draft(draft: ResourceDraft) -> ResourceDraft:
    title = " ".join(draft.title.split())
    resource_type = " ".join(draft.resource_type.casefold().replace("_", " ").split()).replace(
        " ", "_"
    )
    topic = " ".join(draft.topic.split())
    difficulty = (
        " ".join(draft.difficulty.casefold().split()).replace(" ", "-")
        if draft.difficulty
        else None
    )
    source_url = draft.source_url.strip() if draft.source_url else None
    if not title:
        raise InvalidResourceError("Resource title is required")
    if not resource_type:
        raise InvalidResourceError("Resource type is required")
    if not topic:
        raise InvalidResourceError("Topic is required")
    if not 1 <= draft.estimated_duration_minutes <= 300:
        raise InvalidResourceError("Duration must be between 1 and 300 minutes")
    if not 0 <= draft.priority <= 100:
        raise InvalidResourceError("Priority must be between 0 and 100")
    parsed_url = urlparse(source_url) if source_url else None
    if parsed_url and (
        parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc
    ):
        raise InvalidResourceError("Source URL must be a complete http or https URL")
    tags = tuple(
        value
        for value in dict.fromkeys(" ".join(item.split()) for item in draft.tags)
        if value
    )
    return ResourceDraft(
        title=title,
        resource_type=resource_type,
        skill=draft.skill,
        topic=topic,
        difficulty=difficulty,
        estimated_duration_minutes=draft.estimated_duration_minutes,
        source_url=source_url,
        description=draft.description.strip(),
        content_text=draft.content_text.strip(),
        transcript=draft.transcript.strip(),
        notes=draft.notes.strip(),
        tags=tags,
        priority=draft.priority,
    )
