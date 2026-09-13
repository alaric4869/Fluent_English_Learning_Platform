from app.domain.learning_evidence.entities import (
    HistoricalSkillPerformance,
    LearningEvidenceBundle,
    RecordedLearningEvidence,
    Skill,
)
from app.domain.learning_evidence.repository import LearningEvidenceRepository


class LearningEvidenceService:
    def __init__(self, repository: LearningEvidenceRepository) -> None:
        self.repository = repository

    def record(self, bundle: LearningEvidenceBundle) -> RecordedLearningEvidence:
        return self.repository.record(bundle)

    def get_recent_skill_performance(
        self,
        user_key: str,
        skill: Skill,
        limit: int,
    ) -> tuple[HistoricalSkillPerformance, ...]:
        if limit < 1:
            raise ValueError("limit must be positive")
        return self.repository.list_recent_skill_performance(user_key, skill, limit)
