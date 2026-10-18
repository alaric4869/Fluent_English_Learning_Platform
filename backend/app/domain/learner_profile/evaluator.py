from typing import Protocol, Sequence

from app.domain.learning_evidence.entities import HistoricalSkillPerformance, Skill
from app.domain.learner_profile.entities import SkillProfileEvaluation


class SkillEvaluator(Protocol):
    @property
    def algorithm_version(self) -> str: ...

    @property
    def recent_session_limit(self) -> int: ...

    def evaluate(
        self,
        skill: Skill,
        history: Sequence[HistoricalSkillPerformance],
    ) -> SkillProfileEvaluation: ...
