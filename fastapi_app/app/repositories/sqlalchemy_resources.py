from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.learning_evidence.entities import Skill
from app.domain.resources.entities import LearningResourceDetails, ResourceCandidate
from app.models.learning_evidence import LearningResource, StudySession
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
        statement = (
            select(
                LearningResource,
                study_history.c.last_studied_at,
                study_history.c.completed_session_count,
                assignment_history.c.last_assigned_date,
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
        return LearningResourceDetails(
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
            active=resource.active,
        )
