from datetime import date
from typing import Protocol, Sequence

from app.domain.learning_evidence.entities import Skill
from app.domain.resources.entities import ResourceCandidate, ResourceRecommendation
from app.domain.weakness_detection.entities import SkillClassification


class ResourceRecommender(Protocol):
    @property
    def recommender_version(self) -> str: ...

    def recommend(
        self,
        skill: Skill,
        classification: SkillClassification,
        candidates: Sequence[ResourceCandidate],
        target_date: date,
        count: int = 1,
    ) -> tuple[ResourceRecommendation, ...]: ...
