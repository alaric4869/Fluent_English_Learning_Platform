from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.history.entities import HistoricalStudySession
from app.domain.learning_evidence.entities import Skill
from app.models.learning_evidence import LearningResource, StudySession


class SqlAlchemyStudyHistoryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_recent_sessions(
        self,
        user_key: str,
        through: datetime,
        limit: int,
    ) -> tuple[HistoricalStudySession, ...]:
        statement = (
            self._base_statement(user_key)
            .where(StudySession.completed_at < through)
            .order_by(StudySession.completed_at.desc(), StudySession.id.desc())
            .limit(limit)
        )
        return self._execute(statement)

    def list_sessions_between(
        self,
        user_key: str,
        start: datetime,
        end: datetime,
    ) -> tuple[HistoricalStudySession, ...]:
        statement = (
            self._base_statement(user_key)
            .where(
                StudySession.completed_at >= start,
                StudySession.completed_at < end,
            )
            .order_by(StudySession.completed_at, StudySession.id)
        )
        return self._execute(statement)

    def list_all_sessions_through(
        self,
        user_key: str,
        through: datetime,
    ) -> tuple[HistoricalStudySession, ...]:
        statement = (
            self._base_statement(user_key)
            .where(StudySession.completed_at < through)
            .order_by(StudySession.completed_at.desc(), StudySession.id.desc())
        )
        return self._execute(statement)

    @staticmethod
    def _base_statement(user_key: str):
        return (
            select(StudySession, LearningResource.title)
            .join(LearningResource, LearningResource.id == StudySession.resource_id)
            .where(
                StudySession.user_key == user_key,
                StudySession.status == "completed",
            )
        )

    def _execute(self, statement) -> tuple[HistoricalStudySession, ...]:
        return tuple(
            HistoricalStudySession(
                id=session.id,
                resource_id=session.resource_id,
                resource_title=resource_title,
                skill=Skill(session.skill),
                source_type=session.source_type,
                source_id=session.source_id,
                status=session.status,
                started_at=session.started_at,
                completed_at=session.completed_at,
                actual_duration_seconds=session.actual_duration_seconds,
                accuracy=session.accuracy,
                attempt_count=session.attempt_count,
                incorrect_item_count=session.incorrect_item_count,
                notes=session.notes,
            )
            for session, resource_title in self.session.execute(statement)
        )
