from datetime import date, datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.composition import build_application_services
from app.database import Base
from app.domain.learning_evidence.entities import Skill
from app.domain.resources.entities import (
    CompletionFilter,
    ResourceDraft,
    ResourceLibraryFilters,
    ResourceSort,
    ResourceStateChanges,
)
from app.models.learning_evidence import LearningResource, StudySession
from app.services.resources import ResourcePermissionError


def test_personal_resources_can_be_filtered_updated_and_archived_safely() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        services = build_application_services(session)
        resource = services.resources.add_resource(
            "learner",
            _draft("ABC News Conversation", source_url="https://example.com/news"),
        )
        other = services.resources.add_resource(
            "learner",
            _draft("Housing Article", skill=Skill.READING, resource_type="article"),
        )
        services.resources.update_user_state(
            "learner",
            resource.id,
            ResourceStateChanges(favorite=True, saved_for_later=True),
        )
        session.add(
            StudySession(
                user_key="learner",
                resource_id=resource.id,
                skill=Skill.LISTENING.value,
                source_type="manual",
                source_id=str(resource.id),
                source_revision=1,
                status="completed",
                started_at=datetime(2026, 9, 12, 10, tzinfo=timezone.utc),
                completed_at=datetime(2026, 9, 12, 10, 20, tzinfo=timezone.utc),
                actual_duration_seconds=1200,
                accuracy=0.8,
                attempt_count=1,
                incorrect_item_count=2,
                notes="",
            )
        )
        session.commit()

        favorite = services.resources.get_library(
            "learner", ResourceLibraryFilters(favorite_only=True)
        )
        completed = services.resources.get_library(
            "learner",
            ResourceLibraryFilters(completion=CompletionFilter.COMPLETED),
        )
        recently_studied = services.resources.get_library(
            "learner",
            ResourceLibraryFilters(sort=ResourceSort.RECENTLY_STUDIED),
        )
        tag_search = services.resources.get_library(
            "learner", ResourceLibraryFilters(search="natural speech")
        )
        updated = services.resources.update_resource(
            "learner",
            resource.id,
            _draft("ABC News Natural Conversation", priority=80),
        )

        assert [item.id for item in favorite.items] == [resource.id]
        assert [item.id for item in completed.items] == [resource.id]
        assert recently_studied.items[0].id == resource.id
        assert {item.id for item in tag_search.items} == {resource.id, other.id}
        assert updated.title == "ABC News Natural Conversation"
        assert updated.priority == 80
        assert updated.favorite is True
        assert services.resources.get_library("another-user").total_count == 0

        services.resources.update_user_state(
            "learner", resource.id, ResourceStateChanges(archived=True)
        )

        active_ids = {item.id for item in services.resources.get_library("learner").items}
        archived_ids = {
            item.id
            for item in services.resources.get_library(
                "learner", ResourceLibraryFilters(archived_only=True)
            ).items
        }
        candidate_ids = {
            item.id
            for item in services.resources.list_available_for_skill(
                "learner", Skill.LISTENING, date(2026, 9, 13)
            )
        }
        assert resource.id not in active_ids
        assert other.id in active_ids
        assert archived_ids == {resource.id}
        assert resource.id not in candidate_ids

        restored = services.resources.update_user_state(
            "learner", resource.id, ResourceStateChanges(archived=False)
        )
        assert restored.archived is False
        assert resource.id in {
            item.id for item in services.resources.get_library("learner").items
        }


def test_built_in_resource_content_cannot_be_edited() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        built_in = LearningResource(
            slug="built-in",
            title="Built in IELTS",
            resource_type="ielts_listening",
            skill=Skill.LISTENING.value,
            topic="IELTS General Training",
            difficulty="intermediate",
            estimated_duration_minutes=30,
            content={},
            tags=[],
            priority=60,
            active=True,
        )
        session.add(built_in)
        session.commit()
        services = build_application_services(session)

        with pytest.raises(ResourcePermissionError):
            services.resources.update_resource(
                "learner", built_in.id, _draft("Changed")
            )


def _draft(
    title: str,
    *,
    skill: Skill = Skill.LISTENING,
    resource_type: str = "audio",
    source_url: str | None = None,
    priority: int = 50,
) -> ResourceDraft:
    return ResourceDraft(
        title=title,
        resource_type=resource_type,
        skill=skill,
        topic="Australian daily life",
        difficulty="Intermediate",
        estimated_duration_minutes=20,
        source_url=source_url,
        description="Natural conversation practice",
        content_text="",
        transcript="A short transcript.",
        notes="Listen twice before reading.",
        tags=("Australia", "natural speech", "Australia"),
        priority=priority,
    )
