from typing import Protocol

from app.domain.learner_profile.entities import LearnerProfileEvaluation, LearnerProfileSnapshot


class LearnerProfileRepository(Protocol):
    def save_snapshot(self, evaluation: LearnerProfileEvaluation) -> LearnerProfileSnapshot: ...

    def get_latest(self, user_key: str) -> LearnerProfileSnapshot | None: ...
