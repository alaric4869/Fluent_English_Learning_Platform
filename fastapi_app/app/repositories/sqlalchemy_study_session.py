from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.learning_evidence.entities import Skill
from app.domain.study_session.entities import (
    ModuleStudySession,
    SaveModuleSessionCommand,
    StartModuleSessionCommand,
    StudySessionStatus,
)
from app.models.learning_evidence import SkillPerformance, StudySession


SOURCE_TYPE = "study_plan_item"


class SqlAlchemyStudySessionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_latest_for_plan_items(
        self,
        user_key: str,
        study_plan_item_ids: tuple[int, ...],
    ) -> dict[int, ModuleStudySession]:
        if not study_plan_item_ids:
            return {}
        rows = self.session.scalars(
            select(StudySession)
            .where(
                StudySession.user_key == user_key,
                StudySession.source_type == SOURCE_TYPE,
                StudySession.source_id.in_(
                    tuple(str(value) for value in study_plan_item_ids)
                ),
            )
            .order_by(StudySession.source_revision.desc(), StudySession.id.desc())
        )
        latest: dict[int, ModuleStudySession] = {}
        for row in rows:
            item_id = int(row.source_id)
            latest.setdefault(item_id, _to_domain(row))
        return latest

    def start(self, command: StartModuleSessionCommand) -> ModuleStudySession:
        latest = self._get_latest(command.user_key, command.study_plan_item_id)
        if latest is not None and latest.status == StudySessionStatus.IN_PROGRESS.value:
            return _to_domain(latest)
        revision = latest.source_revision + 1 if latest is not None else 1
        row = StudySession(
            user_key=command.user_key,
            resource_id=command.resource_id,
            skill=command.skill.value,
            source_type=SOURCE_TYPE,
            source_id=str(command.study_plan_item_id),
            source_revision=revision,
            status=StudySessionStatus.IN_PROGRESS.value,
            started_at=command.started_at,
            completed_at=None,
            actual_duration_seconds=0,
            perceived_difficulty=None,
            confidence=None,
            accuracy=None,
            attempt_count=1,
            hard_item_count=None,
            incorrect_item_count=0,
            notes="",
            updated_at=command.started_at,
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return _to_domain(row)

    def save_progress(
        self, command: SaveModuleSessionCommand
    ) -> ModuleStudySession:
        row = self._get(command)
        if row.status != StudySessionStatus.IN_PROGRESS.value:
            raise ValueError("Completed study sessions cannot be edited")
        self._apply_progress(row, command)
        self.session.commit()
        self.session.refresh(row)
        return _to_domain(row)

    def complete(self, command: SaveModuleSessionCommand) -> ModuleStudySession:
        row = self._get(command)
        if row.status == StudySessionStatus.COMPLETED.value:
            return _to_domain(row)
        self._apply_progress(row, command)
        row.status = StudySessionStatus.COMPLETED.value
        row.completed_at = command.occurred_at
        performance = self.session.scalar(
            select(SkillPerformance).where(
                SkillPerformance.study_session_id == row.id,
                SkillPerformance.skill == row.skill,
            )
        )
        if performance is None:
            self.session.add(
                SkillPerformance(
                    study_session_id=row.id,
                    user_key=row.user_key,
                    skill=row.skill,
                    accuracy=None,
                    item_count=0,
                    correct_item_count=0,
                    incorrect_item_count=0,
                    hard_item_count=None,
                    confidence=row.confidence,
                    perceived_difficulty=row.perceived_difficulty,
                    occurred_at=command.occurred_at,
                    metrics={
                        "evidence_type": "self_assessment",
                        "active_duration_seconds": row.actual_duration_seconds or 0,
                    },
                )
            )
        self.session.commit()
        self.session.refresh(row)
        return _to_domain(row)

    def _get_latest(
        self, user_key: str, study_plan_item_id: int
    ) -> StudySession | None:
        return self.session.scalar(
            select(StudySession)
            .where(
                StudySession.user_key == user_key,
                StudySession.source_type == SOURCE_TYPE,
                StudySession.source_id == str(study_plan_item_id),
            )
            .order_by(StudySession.source_revision.desc(), StudySession.id.desc())
            .limit(1)
        )

    def _get(self, command: SaveModuleSessionCommand) -> StudySession:
        row = self.session.scalar(
            select(StudySession).where(
                StudySession.id == command.study_session_id,
                StudySession.user_key == command.user_key,
                StudySession.source_type == SOURCE_TYPE,
                StudySession.source_id == str(command.study_plan_item_id),
            )
        )
        if row is None:
            raise LookupError("Study session not found")
        return row

    @staticmethod
    def _apply_progress(
        row: StudySession, command: SaveModuleSessionCommand
    ) -> None:
        progress = command.progress
        row.actual_duration_seconds = max(
            row.actual_duration_seconds or 0,
            progress.active_duration_seconds,
        )
        row.notes = progress.notes
        row.perceived_difficulty = progress.perceived_difficulty
        row.confidence = progress.confidence
        row.updated_at = command.occurred_at


def _to_domain(row: StudySession) -> ModuleStudySession:
    return ModuleStudySession(
        id=row.id,
        user_key=row.user_key,
        study_plan_item_id=int(row.source_id),
        resource_id=row.resource_id,
        skill=Skill(row.skill),
        revision=row.source_revision,
        status=StudySessionStatus(row.status),
        started_at=_as_utc(row.started_at),
        completed_at=_as_utc(row.completed_at),
        active_duration_seconds=row.actual_duration_seconds or 0,
        perceived_difficulty=row.perceived_difficulty,
        confidence=row.confidence,
        notes=row.notes,
        created_at=_as_utc(row.created_at),
        updated_at=_as_utc(row.updated_at),
    )


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
