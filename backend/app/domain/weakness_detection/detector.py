from typing import Protocol, Sequence

from app.domain.learning_evidence.entities import Skill
from app.domain.learner_profile.entities import HistoricalSkillProfile
from app.domain.weakness_detection.entities import SkillWeaknessAssessment


class WeaknessDetector(Protocol):
    @property
    def detector_version(self) -> str: ...

    @property
    def recent_snapshot_limit(self) -> int: ...

    def detect(
        self,
        skill: Skill,
        history: Sequence[HistoricalSkillProfile],
    ) -> SkillWeaknessAssessment: ...
