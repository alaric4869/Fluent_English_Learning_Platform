from dataclasses import dataclass
from datetime import datetime

from app.domain.study_plan.entities import StudyPlanItemStatus


@dataclass(frozen=True)
class StudyPlanItemStatusTransition:
    status: StudyPlanItemStatus
    started_at: datetime | None
    completed_at: datetime | None


def calculate_item_status_transition(
    current_status: StudyPlanItemStatus,
    current_started_at: datetime | None,
    current_completed_at: datetime | None,
    target_status: StudyPlanItemStatus,
    occurred_at: datetime,
) -> StudyPlanItemStatusTransition:
    if target_status is current_status:
        return StudyPlanItemStatusTransition(
            status=current_status,
            started_at=current_started_at,
            completed_at=current_completed_at,
        )

    started_at = current_started_at
    completed_at = None
    if target_status in {
        StudyPlanItemStatus.IN_PROGRESS,
        StudyPlanItemStatus.COMPLETED,
    }:
        started_at = started_at or occurred_at
    if target_status is StudyPlanItemStatus.COMPLETED:
        completed_at = occurred_at

    return StudyPlanItemStatusTransition(
        status=target_status,
        started_at=started_at,
        completed_at=completed_at,
    )
