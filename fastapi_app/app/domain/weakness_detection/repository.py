from typing import Protocol

from app.domain.weakness_detection.entities import (
    WeaknessAssessmentEvaluation,
    WeaknessAssessmentRun,
)


class WeaknessAssessmentRepository(Protocol):
    def save_run(self, evaluation: WeaknessAssessmentEvaluation) -> WeaknessAssessmentRun: ...

    def get_latest(self, user_key: str) -> WeaknessAssessmentRun | None: ...
