from datetime import date

from app.domain.learning_evidence.entities import Skill
from app.domain.resources.entities import ResourceRecommendation
from app.domain.resources.recommender import ResourceRecommender
from app.domain.resources.repository import ResourceRepository
from app.domain.weakness_detection.entities import SkillClassification


class ResourceService:
    def __init__(
        self,
        repository: ResourceRepository,
        recommender: ResourceRecommender,
    ) -> None:
        self.repository = repository
        self.recommender = recommender

    @property
    def recommender_version(self) -> str:
        return self.recommender.recommender_version

    def recommend_for_skill(
        self,
        user_key: str,
        skill: Skill,
        classification: SkillClassification,
        target_date: date,
    ) -> ResourceRecommendation | None:
        candidates = self.repository.list_candidates(user_key, skill, target_date)
        recommendations = self.recommender.recommend(
            skill,
            classification,
            candidates,
            target_date,
            count=1,
        )
        return recommendations[0] if recommendations else None
