from app.domain.learning_evidence.entities import LearningEvidenceBundle, RecordedLearningEvidence
from app.domain.learning_evidence.repository import LearningEvidenceRepository


class LearningEvidenceService:
    def __init__(self, repository: LearningEvidenceRepository) -> None:
        self.repository = repository

    def record(self, bundle: LearningEvidenceBundle) -> RecordedLearningEvidence:
        return self.repository.record(bundle)
