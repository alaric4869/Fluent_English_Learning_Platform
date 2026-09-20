from typing import Protocol

from app.domain.adaptive_learning.entities import (
    AIPlanItemRecommendation,
    AdaptationDecision,
    ManualPlanItemOverride,
)


class AdaptationDecisionRepository(Protocol):
    def apply_manual_override(self, command: ManualPlanItemOverride) -> AdaptationDecision: ...

    def append_ai_recommendation(
        self,
        command: AIPlanItemRecommendation,
    ) -> AdaptationDecision: ...

    def list_for_plan(self, study_plan_id: int) -> tuple[AdaptationDecision, ...]: ...
