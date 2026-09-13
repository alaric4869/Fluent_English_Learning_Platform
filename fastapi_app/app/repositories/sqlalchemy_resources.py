from datetime import date, datetime, timezone

from sqlalchemy import String, and_, cast, func, or_, select
from sqlalchemy.orm import Session

from app.domain.learning_evidence.entities import Skill
from app.domain.resources.entities import (
    CompletionFilter,
    LearningResourceDetails,
    ResourceCandidate,
    ResourceDraft,
    ResourceLibraryFacets,
    ResourceLibraryFilters,
    ResourceSort,
    ResourceStateChanges,
)
from app.models.learning_evidence import (
    LearningResource,
    ResourceUserState,
    StudySession,
)
from app.models.study_plan import StudyPlanItemModel, StudyPlanModel


class SqlAlchemyResourceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_candidates(
        self,
        user_key: str,
        skill: Skill,
        target_date: date,
    ) -> tuple[ResourceCandidate, ...]:
        study_history = (
            select(
                StudySession.resource_id.label("resource_id"),
                func.max(StudySession.completed_at).label("last_studied_at"),
                func.count(StudySession.id).label("completed_session_count"),
            )
            .where(
                StudySession.user_key == user_key,
                func.date(StudySession.completed_at) < target_date,
            )
            .group_by(StudySession.resource_id)
            .subquery()
        )
        assignment_history = (
            select(
                StudyPlanItemModel.resource_id.label("resource_id"),
                func.max(StudyPlanModel.plan_date).label("last_assigned_date"),
            )
            .join(StudyPlanModel, StudyPlanModel.id == StudyPlanItemModel.study_plan_id)
            .where(
                StudyPlanModel.user_key == user_key,
                StudyPlanModel.plan_date < target_date,
                StudyPlanItemModel.resource_id.is_not(None),
            )
            .group_by(StudyPlanItemModel.resource_id)
            .subquery()
        )
        user_state = self._user_state(user_key)
        statement = (
            select(
                LearningResource,
                study_history.c.last_studied_at,
                study_history.c.completed_session_count,
                assignment_history.c.last_assigned_date,
            )
            .outerjoin(
                user_state,
                user_state.c.resource_id == LearningResource.id,
            )
            .outerjoin(
                study_history,
                study_history.c.resource_id == LearningResource.id,
            )
            .outerjoin(
                assignment_history,
                assignment_history.c.resource_id == LearningResource.id,
            )
            .where(
                LearningResource.active.is_(True),
                LearningResource.skill == skill.value,
                or_(
                    LearningResource.owner_user_key.is_(None),
                    LearningResource.owner_user_key == user_key,
                ),
                user_state.c.archived_at.is_(None),
            )
            .order_by(LearningResource.priority.desc(), LearningResource.id)
        )
        return tuple(
            ResourceCandidate(
                id=resource.id,
                slug=resource.slug,
                title=resource.title,
                resource_type=resource.resource_type,
                skill=Skill(resource.skill),
                topic=resource.topic,
                difficulty=resource.difficulty,
                estimated_duration_minutes=resource.estimated_duration_minutes,
                priority=resource.priority,
                tags=tuple(resource.tags),
                last_studied_at=last_studied_at,
                last_assigned_date=last_assigned_date,
                completed_session_count=completed_session_count or 0,
            )
            for (
                resource,
                last_studied_at,
                completed_session_count,
                last_assigned_date,
            ) in self.session.execute(statement)
        )

    def get(self, resource_id: int) -> LearningResourceDetails | None:
        resource = self.session.get(LearningResource, resource_id)
        if resource is None:
            return None
        return self._to_details(resource)

    def get_for_user(
        self,
        user_key: str,
        resource_id: int,
    ) -> LearningResourceDetails | None:
        history = self._study_history(user_key)
        statement = (
            select(
                LearningResource,
                ResourceUserState,
                history.c.last_studied_at,
                history.c.completed_session_count,
            )
            .outerjoin(
                ResourceUserState,
                and_(
                    ResourceUserState.resource_id == LearningResource.id,
                    ResourceUserState.user_key == user_key,
                ),
            )
            .outerjoin(history, history.c.resource_id == LearningResource.id)
            .where(
                LearningResource.id == resource_id,
                LearningResource.active.is_(True),
                or_(
                    LearningResource.owner_user_key.is_(None),
                    LearningResource.owner_user_key == user_key,
                ),
            )
        )
        row = self.session.execute(statement).one_or_none()
        return self._to_details(*row) if row else None

    def list_library(
        self,
        user_key: str,
        filters: ResourceLibraryFilters,
        limit: int,
    ) -> tuple[LearningResourceDetails, ...]:
        statement = self._library_statement(user_key, filters)
        return tuple(
            self._to_details(resource, state, last_studied_at, completed_count or 0)
            for resource, state, last_studied_at, completed_count in self.session.execute(
                statement.limit(limit)
            )
        )

    def count_library(self, user_key: str, filters: ResourceLibraryFilters) -> int:
        statement = self._library_statement(user_key, filters).order_by(None).subquery()
        return self.session.scalar(select(func.count()).select_from(statement)) or 0

    def get_facets(self, user_key: str) -> ResourceLibraryFacets:
        state = self._user_state(user_key)
        visible = (
            LearningResource.active.is_(True),
            or_(
                LearningResource.owner_user_key.is_(None),
                LearningResource.owner_user_key == user_key,
            ),
            state.c.archived_at.is_(None),
        )

        def values(column) -> tuple[str, ...]:
            statement = (
                select(column)
                .outerjoin(state, state.c.resource_id == LearningResource.id)
                .where(*visible, column.is_not(None), column != "")
                .distinct()
                .order_by(column)
            )
            return tuple(self.session.scalars(statement))

        return ResourceLibraryFacets(
            resource_types=values(LearningResource.resource_type),
            topics=values(LearningResource.topic),
            difficulties=values(LearningResource.difficulty),
        )

    def create(
        self,
        user_key: str,
        slug: str,
        draft: ResourceDraft,
    ) -> LearningResourceDetails:
        resource = LearningResource(
            slug=slug,
            title=draft.title,
            resource_type=draft.resource_type,
            skill=draft.skill.value,
            topic=draft.topic,
            difficulty=draft.difficulty,
            estimated_duration_minutes=draft.estimated_duration_minutes,
            source_url=draft.source_url,
            local_asset_reference=None,
            content={},
            tags=list(draft.tags),
            priority=draft.priority,
            active=True,
            owner_user_key=user_key,
            description=draft.description,
            content_text=draft.content_text,
            transcript=draft.transcript,
            notes=draft.notes,
        )
        self.session.add(resource)
        self.session.commit()
        saved = self.get_for_user(user_key, resource.id)
        if saved is None:
            raise RuntimeError("Resource disappeared after it was created")
        return saved

    def update(
        self,
        user_key: str,
        resource_id: int,
        draft: ResourceDraft,
    ) -> LearningResourceDetails | None:
        resource = self.session.scalar(
            select(LearningResource).where(
                LearningResource.id == resource_id,
                LearningResource.owner_user_key == user_key,
            )
        )
        if resource is None:
            return None
        resource.title = draft.title
        resource.resource_type = draft.resource_type
        resource.skill = draft.skill.value
        resource.topic = draft.topic
        resource.difficulty = draft.difficulty
        resource.estimated_duration_minutes = draft.estimated_duration_minutes
        resource.source_url = draft.source_url
        resource.description = draft.description
        resource.content_text = draft.content_text
        resource.transcript = draft.transcript
        resource.notes = draft.notes
        resource.tags = list(draft.tags)
        resource.priority = draft.priority
        self.session.commit()
        return self.get_for_user(user_key, resource.id)

    def set_user_state(
        self,
        user_key: str,
        resource_id: int,
        changes: ResourceStateChanges,
    ) -> LearningResourceDetails | None:
        resource = self.session.scalar(
            select(LearningResource).where(
                LearningResource.id == resource_id,
                LearningResource.active.is_(True),
                or_(
                    LearningResource.owner_user_key.is_(None),
                    LearningResource.owner_user_key == user_key,
                ),
            )
        )
        if resource is None:
            return None
        state = self.session.scalar(
            select(ResourceUserState).where(
                ResourceUserState.user_key == user_key,
                ResourceUserState.resource_id == resource_id,
            )
        )
        if state is None:
            state = ResourceUserState(user_key=user_key, resource_id=resource_id)
            self.session.add(state)
        if changes.favorite is not None:
            state.favorite = changes.favorite
        if changes.saved_for_later is not None:
            state.saved_for_later = changes.saved_for_later
        if changes.archived is not None:
            state.archived_at = datetime.now(timezone.utc) if changes.archived else None
        self.session.commit()
        return self.get_for_user(user_key, resource_id)

    def _library_statement(
        self,
        user_key: str,
        filters: ResourceLibraryFilters,
    ):
        history = self._study_history(user_key)
        statement = (
            select(
                LearningResource,
                ResourceUserState,
                history.c.last_studied_at,
                history.c.completed_session_count,
            )
            .outerjoin(
                ResourceUserState,
                and_(
                    ResourceUserState.resource_id == LearningResource.id,
                    ResourceUserState.user_key == user_key,
                ),
            )
            .outerjoin(history, history.c.resource_id == LearningResource.id)
            .where(
                LearningResource.active.is_(True),
                or_(
                    LearningResource.owner_user_key.is_(None),
                    LearningResource.owner_user_key == user_key,
                ),
            )
        )
        if filters.archived_only:
            statement = statement.where(ResourceUserState.archived_at.is_not(None))
        else:
            statement = statement.where(ResourceUserState.archived_at.is_(None))
        if filters.search:
            pattern = f"%{filters.search.casefold()}%"
            statement = statement.where(
                or_(
                    func.lower(LearningResource.title).like(pattern),
                    func.lower(LearningResource.description).like(pattern),
                    func.lower(LearningResource.content_text).like(pattern),
                    func.lower(LearningResource.transcript).like(pattern),
                    func.lower(LearningResource.notes).like(pattern),
                    func.lower(LearningResource.topic).like(pattern),
                    func.lower(cast(LearningResource.tags, String)).like(pattern),
                )
            )
        if filters.skill is not None:
            statement = statement.where(LearningResource.skill == filters.skill.value)
        if filters.resource_type:
            statement = statement.where(
                LearningResource.resource_type == filters.resource_type
            )
        if filters.topic:
            statement = statement.where(LearningResource.topic == filters.topic)
        if filters.difficulty:
            statement = statement.where(
                LearningResource.difficulty == filters.difficulty
            )
        if filters.completion is CompletionFilter.COMPLETED:
            statement = statement.where(history.c.completed_session_count > 0)
        elif filters.completion is CompletionFilter.NOT_COMPLETED:
            statement = statement.where(history.c.completed_session_count.is_(None))
        if filters.favorite_only:
            statement = statement.where(ResourceUserState.favorite.is_(True))
        if filters.saved_for_later_only:
            statement = statement.where(ResourceUserState.saved_for_later.is_(True))

        if filters.sort is ResourceSort.RECENTLY_STUDIED:
            return statement.order_by(
                history.c.last_studied_at.desc().nullslast(),
                LearningResource.id.desc(),
            )
        if filters.sort is ResourceSort.TITLE:
            return statement.order_by(func.lower(LearningResource.title), LearningResource.id)
        if filters.sort is ResourceSort.PRIORITY:
            return statement.order_by(
                LearningResource.priority.desc(), LearningResource.id.desc()
            )
        return statement.order_by(
            LearningResource.created_at.desc(), LearningResource.id.desc()
        )

    @staticmethod
    def _study_history(user_key: str):
        return (
            select(
                StudySession.resource_id.label("resource_id"),
                func.max(StudySession.completed_at).label("last_studied_at"),
                func.count(StudySession.id).label("completed_session_count"),
            )
            .where(StudySession.user_key == user_key)
            .group_by(StudySession.resource_id)
            .subquery()
        )

    @staticmethod
    def _user_state(user_key: str):
        return (
            select(
                ResourceUserState.resource_id.label("resource_id"),
                ResourceUserState.favorite.label("favorite"),
                ResourceUserState.saved_for_later.label("saved_for_later"),
                ResourceUserState.archived_at.label("archived_at"),
            )
            .where(ResourceUserState.user_key == user_key)
            .subquery()
        )

    @staticmethod
    def _to_details(
        resource: LearningResource,
        state: ResourceUserState | None = None,
        last_studied_at: datetime | None = None,
        completed_session_count: int | None = 0,
    ) -> LearningResourceDetails:
        return LearningResourceDetails(
            id=resource.id,
            slug=resource.slug,
            title=resource.title,
            resource_type=resource.resource_type,
            skill=Skill(resource.skill),
            topic=resource.topic,
            difficulty=resource.difficulty,
            estimated_duration_minutes=resource.estimated_duration_minutes,
            source_url=resource.source_url,
            content=dict(resource.content),
            priority=resource.priority,
            tags=tuple(resource.tags),
            active=resource.active,
            owner_user_key=resource.owner_user_key,
            description=resource.description,
            content_text=resource.content_text,
            transcript=resource.transcript,
            notes=resource.notes,
            favorite=state.favorite if state else False,
            saved_for_later=state.saved_for_later if state else False,
            archived=state.archived_at is not None if state else False,
            last_studied_at=_as_utc(last_studied_at),
            completed_session_count=completed_session_count or 0,
            created_at=_as_utc(resource.created_at),
            updated_at=_as_utc(resource.updated_at),
        )


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
