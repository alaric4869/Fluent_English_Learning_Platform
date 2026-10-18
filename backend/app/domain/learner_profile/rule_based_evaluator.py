from statistics import mean
from typing import Sequence

from app.domain.learning_evidence.entities import HistoricalSkillPerformance, Skill
from app.domain.learner_profile.config import (
    DEFAULT_LEARNER_PROFILE_CONFIG,
    LearnerProfileConfig,
)
from app.domain.learner_profile.entities import (
    EvidenceStatus,
    SkillProfileEvaluation,
)


SKILL_LABELS = {
    Skill.LISTENING: "听力",
    Skill.SPEAKING: "口语",
    Skill.READING: "阅读",
    Skill.WRITING: "写作",
    Skill.VOCABULARY: "词汇",
}


class RuleBasedSkillEvaluator:
    def __init__(self, config: LearnerProfileConfig = DEFAULT_LEARNER_PROFILE_CONFIG) -> None:
        self.config = config

    @property
    def algorithm_version(self) -> str:
        return self.config.algorithm_version

    @property
    def recent_session_limit(self) -> int:
        return self.config.recent_session_limit

    def evaluate(
        self,
        skill: Skill,
        history: Sequence[HistoricalSkillPerformance],
    ) -> SkillProfileEvaluation:
        recent = sorted(history, key=lambda item: (item.occurred_at, item.id))[
            -self.config.recent_session_limit :
        ]
        if not recent:
            return SkillProfileEvaluation(
                skill=skill,
                score=None,
                evidence_status=EvidenceStatus.NO_DATA,
                sample_count=0,
                average_accuracy=None,
                average_confidence=None,
                average_difficulty=None,
                hard_item_rate=None,
                accuracy_trend=None,
                evidence_ids=(),
                calculation_weights={},
                explanation=f"{SKILL_LABELS[skill]}暂无已完成的学习数据，暂不计算分数。",
            )

        accuracy_values = [
            _clamp(item.accuracy, 0.0, 1.0)
            for item in recent
            if item.accuracy is not None
        ]
        average_accuracy = mean(accuracy_values) if accuracy_values else None
        confidence_values = [item.confidence for item in recent if item.confidence is not None]
        difficulty_values = [
            item.perceived_difficulty
            for item in recent
            if item.perceived_difficulty is not None
        ]
        hard_item_rate = _hard_item_rate(recent)
        average_confidence = mean(confidence_values) if confidence_values else None
        average_difficulty = mean(difficulty_values) if difficulty_values else None
        score, weights = self._calculate_score(
            average_accuracy,
            average_confidence,
            average_difficulty,
            hard_item_rate,
        )
        scored_sample_count = sum(
            item.accuracy is not None
            or item.confidence is not None
            or item.perceived_difficulty is not None
            or item.hard_item_count is not None
            for item in recent
        )
        evidence_status = (
            EvidenceStatus.ESTABLISHED
            if score is not None
            and scored_sample_count >= self.config.minimum_established_samples
            else EvidenceStatus.PROVISIONAL
        )
        trend = self._accuracy_trend(recent)
        explanation = self._explain(
            skill=skill,
            score=score,
            status=evidence_status,
            sample_count=len(recent),
            average_accuracy=average_accuracy,
            average_confidence=average_confidence,
            average_difficulty=average_difficulty,
            hard_item_rate=hard_item_rate,
            trend=trend,
        )
        return SkillProfileEvaluation(
            skill=skill,
            score=score,
            evidence_status=evidence_status,
            sample_count=len(recent),
            average_accuracy=average_accuracy,
            average_confidence=average_confidence,
            average_difficulty=average_difficulty,
            hard_item_rate=hard_item_rate,
            accuracy_trend=trend,
            evidence_ids=tuple(item.id for item in recent),
            calculation_weights=weights,
            explanation=explanation,
        )

    def _calculate_score(
        self,
        accuracy: float | None,
        confidence: float | None,
        difficulty: float | None,
        hard_item_rate: float | None,
    ) -> tuple[float | None, dict[str, float]]:
        if accuracy is not None:
            components = {
                "accuracy": (accuracy * 100, self.config.accuracy_weight)
            }
            if confidence is not None:
                components["confidence"] = (
                    _clamp(confidence, 1.0, 5.0) / 5 * 100,
                    self.config.confidence_weight,
                )
            if hard_item_rate is not None:
                components["hard_item_resilience"] = (
                    (1 - _clamp(hard_item_rate, 0.0, 1.0)) * 100,
                    self.config.hard_item_weight,
                )
        else:
            components = {}
            if confidence is not None:
                components["self_confidence"] = (
                    _clamp(confidence, 1.0, 5.0) / 5 * 100,
                    self.config.subjective_confidence_weight,
                )
            if difficulty is not None:
                components["perceived_ease"] = (
                    (6 - _clamp(difficulty, 1.0, 5.0)) / 5 * 100,
                    self.config.subjective_difficulty_weight,
                )
        if not components:
            return None, {}
        total_weight = sum(weight for _, weight in components.values())
        normalized_weights = {
            name: weight / total_weight for name, (_, weight) in components.items()
        }
        score = sum(
            value * normalized_weights[name]
            for name, (value, _) in components.items()
        )
        return round(score, self.config.score_precision), normalized_weights

    def _accuracy_trend(
        self,
        history: Sequence[HistoricalSkillPerformance],
    ) -> float | None:
        measured = tuple(item for item in history if item.accuracy is not None)
        if len(measured) < self.config.minimum_trend_samples:
            return None
        midpoint = len(measured) // 2
        older = mean(
            _clamp(item.accuracy, 0.0, 1.0)
            for item in measured[:midpoint]
            if item.accuracy is not None
        )
        newer = mean(
            _clamp(item.accuracy, 0.0, 1.0)
            for item in measured[midpoint:]
            if item.accuracy is not None
        )
        return round(newer - older, 4)

    def _explain(
        self,
        *,
        skill: Skill,
        score: float | None,
        status: EvidenceStatus,
        sample_count: int,
        average_accuracy: float | None,
        average_confidence: float | None,
        average_difficulty: float | None,
        hard_item_rate: float | None,
        trend: float | None,
    ) -> str:
        label = SKILL_LABELS[skill]
        prefix = "暂定" if status is EvidenceStatus.PROVISIONAL else "当前"
        if score is None:
            return (
                f"{label}已有 {sample_count} 次学习记录，但尚未提供正确率、难度或信心，"
                "因此暂不计算分数。"
            )
        parts = [f"{label}{prefix}分数为 {score:.1f}，依据最近 {sample_count} 次学习"]
        if average_accuracy is not None:
            parts.append(f"平均正确率为 {average_accuracy * 100:.1f}%")
        else:
            parts.append("本分数仅依据你的难度与信心自评，不等同于客观正确率")
        if average_confidence is not None:
            parts.append(f"平均信心为 {average_confidence:.1f}/5")
        if average_difficulty is not None:
            parts.append(f"平均难度为 {average_difficulty:.1f}/5")
        if hard_item_rate is not None:
            parts.append(f"难题比例为 {hard_item_rate * 100:.1f}%")
        if trend is not None:
            direction = "上升" if trend > 0 else "下降" if trend < 0 else "持平"
            parts.append(f"近期正确率趋势{direction} {abs(trend) * 100:.1f} 个百分点")
        explanation = "；".join(parts) + "。缺失的指标不会参与权重计算。"
        if status is EvidenceStatus.PROVISIONAL:
            explanation += (
                f"至少需要 {self.config.minimum_established_samples} 次数据后才标记为已建立。"
            )
        return explanation


def _hard_item_rate(history: Sequence[HistoricalSkillPerformance]) -> float | None:
    measured = [item for item in history if item.hard_item_count is not None]
    item_count = sum(item.item_count for item in measured)
    if not measured or not item_count:
        return None
    rate = sum(item.hard_item_count or 0 for item in measured) / item_count
    return _clamp(rate, 0.0, 1.0)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return min(maximum, max(minimum, value))
