from collections.abc import Callable
from datetime import date, datetime, timezone

from app.domain.study_plan.entities import (
    DailyStudyPlan,
    DailyStudyPlanItem,
    StudyPlanItemStatus,
)
from app.domain.study_session.entities import (
    ModuleStudySession,
    SaveModuleSessionCommand,
    StartModuleSessionCommand,
    StudySessionProgress,
    StudySessionStatus,
)
from app.domain.study_session.repository import StudySessionRepository
from app.services.learner_profile import LearnerProfileService
from app.services.study_plan import StudyPlanService
from app.services.weakness_detection import WeaknessDetectionService


class InvalidStudySessionError(ValueError):
    pass


class StudySessionService:
    def __init__(
        self,
        repository: StudySessionRepository,
        study_plan_service: StudyPlanService,
        learner_profile_service: LearnerProfileService,
        weakness_detection_service: WeaknessDetectionService,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.repository = repository
        self.study_plan_service = study_plan_service
        self.learner_profile_service = learner_profile_service
        self.weakness_detection_service = weakness_detection_service
        self.now = now or utc_now

    def get_latest_for_plan(
        self, user_key: str, plan_date: date
    ) -> dict[int, ModuleStudySession]:
        plan = self.study_plan_service.get_daily_plan(user_key, plan_date)
        if plan is None:
            return {}
        return self.repository.get_latest_for_plan_items(
            user_key, tuple(item.id for item in plan.items)
        )

    def start(
        self,
        user_key: str,
        plan_date: date,
        study_plan_item_id: int,
    ) -> ModuleStudySession:
        plan, item = self._get_plan_item(user_key, plan_date, study_plan_item_id)
        if item.status is StudyPlanItemStatus.COMPLETED:
            raise InvalidStudySessionError(
                "Reopen the completed module before starting another session"
            )
        if item.resource_id is None:
            raise InvalidStudySessionError("Choose a learning resource first")
        result = self.repository.start(
            StartModuleSessionCommand(
                user_key=user_key,
                study_plan_item_id=item.id,
                resource_id=item.resource_id,
                skill=item.skill,
                started_at=self.now(),
            )
        )
        if item.status is StudyPlanItemStatus.PENDING:
            self.study_plan_service.update_item_status(
                user_key,
                plan.plan_date,
                item.id,
                StudyPlanItemStatus.IN_PROGRESS,
            )
        return result

    def validate_resource_override(
        self,
        user_key: str,
        plan_date: date,
        study_plan_item_id: int,
        new_resource_id: int | None,
    ) -> None:
        plan, item = self._get_plan_item(user_key, plan_date, study_plan_item_id)
        if item.resource_id == new_resource_id:
            return
        latest = self.repository.get_latest_for_plan_items(user_key, (item.id,)).get(
            item.id
        )
        if item.status is StudyPlanItemStatus.COMPLETED:
            raise InvalidStudySessionError(
                "Reopen the completed module before replacing its resource"
            )
        if latest is not None and latest.status is StudySessionStatus.IN_PROGRESS:
            raise InvalidStudySessionError(
                "Complete the active study session before replacing its resource"
            )

    def save_progress(
        self,
        user_key: str,
        plan_date: date,
        study_plan_item_id: int,
        study_session_id: int,
        progress: StudySessionProgress,
    ) -> ModuleStudySession:
        self._get_plan_item(user_key, plan_date, study_plan_item_id)
        return self.repository.save_progress(
            self._command(
                user_key, study_plan_item_id, study_session_id, progress
            )
        )

    def complete(
        self,
        user_key: str,
        plan_date: date,
        study_plan_item_id: int,
        study_session_id: int,
        progress: StudySessionProgress,
    ) -> ModuleStudySession:
        plan, item = self._get_plan_item(user_key, plan_date, study_plan_item_id)
        result = self.repository.complete(
            self._command(
                user_key, study_plan_item_id, study_session_id, progress
            )
        )
        if item.status is not StudyPlanItemStatus.COMPLETED:
            self.study_plan_service.update_item_status(
                user_key,
                plan.plan_date,
                item.id,
                StudyPlanItemStatus.COMPLETED,
            )
        self.learner_profile_service.refresh_profile(user_key)
        self.weakness_detection_service.refresh_assessment(user_key)
        return result

    def _get_plan_item(
        self, user_key: str, plan_date: date, study_plan_item_id: int
    ) -> tuple[DailyStudyPlan, DailyStudyPlanItem]:
        plan = self.study_plan_service.get_daily_plan(user_key, plan_date)
        if plan is None:
            raise LookupError("Study plan not found")
        item = next(
            (value for value in plan.items if value.id == study_plan_item_id),
            None,
        )
        if item is None:
            raise LookupError("Study plan item not found")
        return plan, item

    def _command(
        self,
        user_key: str,
        study_plan_item_id: int,
        study_session_id: int,
        progress: StudySessionProgress,
    ) -> SaveModuleSessionCommand:
        return SaveModuleSessionCommand(
            user_key=user_key,
            study_plan_item_id=study_plan_item_id,
            study_session_id=study_session_id,
            progress=_validate_progress(progress),
            occurred_at=self.now(),
        )


def _validate_progress(progress: StudySessionProgress) -> StudySessionProgress:
    if not 0 <= progress.active_duration_seconds <= 28_800:
        raise InvalidStudySessionError("Active duration must be between 0 and 8 hours")
    if len(progress.notes) > 12_000:
        raise InvalidStudySessionError("Notes must be 12,000 characters or fewer")
    for name, value in (
        ("Difficulty", progress.perceived_difficulty),
        ("Confidence", progress.confidence),
    ):
        if value is not None and not 1 <= value <= 5:
            raise InvalidStudySessionError(f"{name} must be between 1 and 5")
    return StudySessionProgress(
        active_duration_seconds=progress.active_duration_seconds,
        notes=progress.notes.strip(),
        perceived_difficulty=progress.perceived_difficulty,
        confidence=progress.confidence,
    )


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
