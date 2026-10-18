from datetime import datetime
from typing import Protocol

from app.domain.history.entities import HistoricalStudySession


class StudyHistoryRepository(Protocol):
    def list_recent_sessions(
        self,
        user_key: str,
        through: datetime,
        limit: int,
    ) -> tuple[HistoricalStudySession, ...]: ...

    def list_sessions_between(
        self,
        user_key: str,
        start: datetime,
        end: datetime,
    ) -> tuple[HistoricalStudySession, ...]: ...

    def list_all_sessions_through(
        self,
        user_key: str,
        through: datetime,
    ) -> tuple[HistoricalStudySession, ...]: ...
