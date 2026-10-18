from datetime import date, datetime, timezone
from typing import Sequence

from app.domain.learning_evidence.entities import Skill
from app.domain.resources.config import (
    DEFAULT_RESOURCE_RECOMMENDATION_CONFIG,
    DIFFICULTY_RANKS,
    TARGET_DIFFICULTY_RANKS,
    ResourceRecommendationConfig,
)
from app.domain.resources.entities import ResourceCandidate, ResourceRecommendation
from app.domain.weakness_detection.entities import SkillClassification


class RuleBasedResourceRecommender:
    def __init__(
        self,
        config: ResourceRecommendationConfig = DEFAULT_RESOURCE_RECOMMENDATION_CONFIG,
    ) -> None:
        self.config = config

    @property
    def recommender_version(self) -> str:
        return self.config.recommender_version

    def recommend(
        self,
        skill: Skill,
        classification: SkillClassification,
        candidates: Sequence[ResourceCandidate],
        target_date: date,
        count: int = 1,
    ) -> tuple[ResourceRecommendation, ...]:
        if count < 1:
            raise ValueError("count must be positive")
        ranked = sorted(
            (
                self._score(candidate, classification, target_date)
                for candidate in candidates
                if candidate.skill is skill
            ),
            key=lambda item: (-item[0], item[1].id),
        )
        return tuple(
            ResourceRecommendation(
                resource_id=candidate.id,
                score=round(score, 1),
                reasons=tuple(reasons),
            )
            for score, candidate, reasons in ranked[:count]
        )

    def _score(
        self,
        candidate: ResourceCandidate,
        classification: SkillClassification,
        target_date: date,
    ) -> tuple[float, ResourceCandidate, list[str]]:
        score = float(candidate.priority)
        reasons = [f"资源优先级为 {candidate.priority}。"]
        if candidate.last_studied_at is None:
            score += self.config.unused_bonus
            reasons.append("该资源尚未学习，优先用于每日轮换。")
        else:
            age_days = max(
                0,
                (target_date - _as_utc(candidate.last_studied_at).date()).days,
            )
            if age_days < 7:
                score -= self.config.studied_within_7_days_penalty
                reasons.append(f"最近一次学习在 {age_days} 天前，降低重复出现优先级。")
            elif age_days < 30:
                score -= self.config.studied_within_30_days_penalty
                reasons.append(f"最近一次学习在 {age_days} 天前，小幅降低重复优先级。")
            else:
                reasons.append(f"已间隔 {age_days} 天，可以再次安排。")

        if candidate.last_assigned_date is not None:
            assigned_age_days = max(0, (target_date - candidate.last_assigned_date).days)
            if assigned_age_days <= 1:
                score -= self.config.assigned_previous_day_penalty
                reasons.append("该资源刚在前一天的计划中出现，优先轮换其他材料。")
            elif assigned_age_days < 7:
                score -= self.config.assigned_within_7_days_penalty
                reasons.append(
                    f"该资源在 {assigned_age_days} 天前的计划中出现，降低重复安排优先级。"
                )

        difficulty_rank = DIFFICULTY_RANKS.get((candidate.difficulty or "").lower())
        if difficulty_rank is not None:
            target_rank = TARGET_DIFFICULTY_RANKS[classification]
            distance = abs(difficulty_rank - target_rank)
            difficulty_score = max(
                0.0,
                self.config.exact_difficulty_bonus
                - distance * self.config.difficulty_distance_penalty,
            )
            score += difficulty_score
            reasons.append(
                f"难度 {candidate.difficulty} 与当前 {classification.value} 状态的目标难度匹配度贡献 "
                f"{difficulty_score:.1f} 分。"
            )
        else:
            reasons.append("资源未提供标准难度，不使用难度加分。")
        return score, candidate, reasons


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
