from typing import Protocol

from app.domain.learning_evidence.entities import LearningEvidenceBundle, RecordedLearningEvidence


class LearningEvidenceRepository(Protocol):
    def record(self, bundle: LearningEvidenceBundle) -> RecordedLearningEvidence: ...
