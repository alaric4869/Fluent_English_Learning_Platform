from typing import Protocol

from app.domain.learning_evidence.entities import (
    HistoricalSkillPerformance,
    LearningEvidenceBundle,
    RecordedLearningEvidence,
    Skill,
)


class LearningEvidenceRepository(Protocol):
    def record(self, bundle: LearningEvidenceBundle) -> RecordedLearningEvidence: ...

    def list_recent_skill_performance(
        self,
        user_key: str,
        skill: Skill,
        limit: int,
    ) -> tuple[HistoricalSkillPerformance, ...]: ...
