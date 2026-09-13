from typing import Protocol

from app.domain.learning_evidence.entities import Skill
from app.domain.learner_profile.entities import (
    HistoricalSkillProfile,
    LearnerProfileEvaluation,
    LearnerProfileSnapshot,
)


class LearnerProfileRepository(Protocol):
    def save_snapshot(self, evaluation: LearnerProfileEvaluation) -> LearnerProfileSnapshot: ...

    def get_latest(self, user_key: str) -> LearnerProfileSnapshot | None: ...

    def list_recent_skill_profiles(
        self,
        user_key: str,
        skill: Skill,
        limit: int,
    ) -> tuple[HistoricalSkillProfile, ...]: ...
