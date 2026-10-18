from collections.abc import Sequence

from app.domain.study_plan.entities import StudyPlanItemStatus, StudyPlanStatus


def calculate_plan_status(
    item_statuses: Sequence[StudyPlanItemStatus],
) -> StudyPlanStatus:
    if item_statuses and all(
        status is StudyPlanItemStatus.COMPLETED for status in item_statuses
    ):
        return StudyPlanStatus.COMPLETED
    return StudyPlanStatus.ACTIVE
