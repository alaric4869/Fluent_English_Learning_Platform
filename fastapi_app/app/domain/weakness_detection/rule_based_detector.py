from statistics import mean
from typing import Sequence

from app.domain.learning_evidence.entities import Skill
from app.domain.learner_profile.entities import HistoricalSkillProfile
from app.domain.weakness_detection.config import (
    DEFAULT_WEAKNESS_DETECTION_CONFIG,
    WeaknessDetectionConfig,
)
from app.domain.weakness_detection.entities import (
    SkillClassification,
    SkillWeaknessAssessment,
)


SKILL_LABELS = {
    Skill.LISTENING: "听力",
    Skill.SPEAKING: "口语",
    Skill.READING: "阅读",
    Skill.VOCABULARY: "词汇",
}


class RuleBasedWeaknessDetector:
    def __init__(
        self,
        config: WeaknessDetectionConfig = DEFAULT_WEAKNESS_DETECTION_CONFIG,
    ) -> None:
        self.config = config

    @property
    def detector_version(self) -> str:
        return self.config.detector_version

    @property
    def recent_snapshot_limit(self) -> int:
        return self.config.recent_snapshot_limit

    def detect(
        self,
        skill: Skill,
        history: Sequence[HistoricalSkillProfile],
    ) -> SkillWeaknessAssessment:
        recent = sorted(history, key=lambda item: (item.calculated_at, item.skill_snapshot_id))[
            -self.config.recent_snapshot_limit :
        ]
        scored = [item for item in recent if item.score is not None]
        latest = recent[-1] if recent else None
        evidence_ids = tuple(item.profile_snapshot_id for item in recent)
        if len(scored) < self.config.minimum_scored_snapshots:
            reasons = (
                f"{SKILL_LABELS[skill]}只有 {len(scored)} 个可评分画像快照；"
                f"至少需要 {self.config.minimum_scored_snapshots} 个才能判断强弱。",
            )
            return self._assessment(
                skill,
                SkillClassification.INSUFFICIENT_EVIDENCE,
                None,
                latest,
                len(scored),
                evidence_ids,
                reasons,
            )

        smoothed_score = round(
            mean(item.score for item in scored if item.score is not None),
            self.config.score_precision,
        )
        confirmation = scored[-self.config.confirmation_window :]
        consistently_weak = len(confirmation) == self.config.confirmation_window and all(
            item.score is not None and item.score < self.config.weak_score_below
            for item in confirmation
        )
        consistently_strong = len(confirmation) == self.config.confirmation_window and all(
            item.score is not None and item.score >= self.config.strong_score_at_least
            for item in confirmation
        )
        if smoothed_score < self.config.weak_score_below and consistently_weak:
            classification = SkillClassification.WEAK
        elif smoothed_score < self.config.developing_score_below:
            classification = SkillClassification.DEVELOPING
        elif smoothed_score >= self.config.strong_score_at_least and consistently_strong:
            classification = SkillClassification.STRONG
        else:
            classification = SkillClassification.STABLE
        reasons = self._reasons(
            skill,
            classification,
            smoothed_score,
            latest,
            confirmation,
        )
        return self._assessment(
            skill,
            classification,
            smoothed_score,
            latest,
            len(scored),
            evidence_ids,
            reasons,
        )

    def _reasons(
        self,
        skill: Skill,
        classification: SkillClassification,
        smoothed_score: float,
        latest: HistoricalSkillProfile | None,
        confirmation: list[HistoricalSkillProfile],
    ) -> tuple[str, ...]:
        label = SKILL_LABELS[skill]
        reasons = [
            f"{label}最近画像的平滑分数为 {smoothed_score:.1f}。",
            self._threshold_reason(classification, confirmation),
        ]
        if latest and latest.average_accuracy is not None:
            reasons.append(f"最新画像的平均正确率为 {latest.average_accuracy * 100:.1f}%。")
        if latest and latest.average_confidence is not None:
            reasons.append(f"最新画像的平均信心为 {latest.average_confidence:.1f}/5。")
        if latest and latest.hard_item_rate is not None:
            reasons.append(f"最新画像的难题比例为 {latest.hard_item_rate * 100:.1f}%。")
        if latest and latest.accuracy_trend is not None:
            direction = "上升" if latest.accuracy_trend > 0 else "下降" if latest.accuracy_trend < 0 else "持平"
            reasons.append(
                f"最新正确率趋势{direction} {abs(latest.accuracy_trend) * 100:.1f} 个百分点。"
            )
        return tuple(reasons)

    def _threshold_reason(
        self,
        classification: SkillClassification,
        confirmation: list[HistoricalSkillProfile],
    ) -> str:
        if classification is SkillClassification.WEAK:
            return (
                f"最近 {len(confirmation)} 个快照均低于弱项阈值 "
                f"{self.config.weak_score_below:.1f}。"
            )
        if classification is SkillClassification.STRONG:
            return (
                f"最近 {len(confirmation)} 个快照均达到强项阈值 "
                f"{self.config.strong_score_at_least:.1f}。"
            )
        if classification is SkillClassification.DEVELOPING:
            return f"平滑分数低于发展阈值 {self.config.developing_score_below:.1f}。"
        return (
            f"当前证据未持续达到强项阈值 {self.config.strong_score_at_least:.1f}，"
            f"也未持续低于弱项阈值 {self.config.weak_score_below:.1f}。"
        )

    @staticmethod
    def _assessment(
        skill: Skill,
        classification: SkillClassification,
        smoothed_score: float | None,
        latest: HistoricalSkillProfile | None,
        scored_snapshot_count: int,
        evidence_snapshot_ids: tuple[int, ...],
        reasons: tuple[str, ...],
    ) -> SkillWeaknessAssessment:
        return SkillWeaknessAssessment(
            skill=skill,
            classification=classification,
            smoothed_score=smoothed_score,
            latest_score=latest.score if latest else None,
            scored_snapshot_count=scored_snapshot_count,
            latest_average_accuracy=latest.average_accuracy if latest else None,
            latest_average_confidence=latest.average_confidence if latest else None,
            latest_hard_item_rate=latest.hard_item_rate if latest else None,
            latest_accuracy_trend=latest.accuracy_trend if latest else None,
            evidence_snapshot_ids=evidence_snapshot_ids,
            reasons=reasons,
        )
