from datetime import datetime, timedelta, timezone

from app.domain.learning_evidence.entities import Skill
from app.domain.learner_profile.entities import EvidenceStatus, HistoricalSkillProfile
from app.domain.weakness_detection.entities import SkillClassification
from app.domain.weakness_detection.rule_based_detector import RuleBasedWeaknessDetector


NOW = datetime(2026, 9, 13, tzinfo=timezone.utc)


def test_missing_or_single_snapshot_is_not_called_weak() -> None:
    detector = RuleBasedWeaknessDetector()

    no_data = detector.detect(Skill.SPEAKING, [])
    one_low_score = detector.detect(
        Skill.LISTENING,
        [_profile(1, 30.0, skill=Skill.LISTENING)],
    )

    assert no_data.classification is SkillClassification.INSUFFICIENT_EVIDENCE
    assert one_low_score.classification is SkillClassification.INSUFFICIENT_EVIDENCE
    assert one_low_score.smoothed_score is None
    assert "至少需要 2 个" in one_low_score.reasons[0]


def test_two_consistently_low_snapshots_are_classified_as_weak() -> None:
    result = RuleBasedWeaknessDetector().detect(
        Skill.LISTENING,
        [
            _profile(1, 50.0, skill=Skill.LISTENING),
            _profile(
                2,
                52.0,
                skill=Skill.LISTENING,
                average_accuracy=0.48,
                average_confidence=2.4,
                hard_item_rate=0.43,
                accuracy_trend=-0.08,
            ),
        ],
    )

    assert result.classification is SkillClassification.WEAK
    assert result.smoothed_score == 51.0
    assert result.latest_score == 52.0
    assert result.evidence_snapshot_ids == (1, 2)
    assert any("平均正确率为 48.0%" in reason for reason in result.reasons)
    assert any("平均信心为 2.4/5" in reason for reason in result.reasons)
    assert any("难题比例为 43.0%" in reason for reason in result.reasons)
    assert any("下降 8.0 个百分点" in reason for reason in result.reasons)


def test_one_poor_snapshot_does_not_immediately_flip_a_strong_history_to_weak() -> None:
    result = RuleBasedWeaknessDetector().detect(
        Skill.READING,
        [_profile(1, 90.0), _profile(2, 91.0), _profile(3, 30.0)],
    )

    assert result.classification is SkillClassification.STABLE
    assert result.smoothed_score == 70.3


def test_strong_classification_also_requires_confirmation() -> None:
    detector = RuleBasedWeaknessDetector()

    confirmed = detector.detect(
        Skill.READING,
        [_profile(1, 88.0), _profile(2, 90.0)],
    )
    unconfirmed = detector.detect(
        Skill.READING,
        [_profile(1, 70.0), _profile(2, 90.0)],
    )

    assert confirmed.classification is SkillClassification.STRONG
    assert unconfirmed.classification is SkillClassification.STABLE


def _profile(
    identifier: int,
    score: float,
    *,
    skill: Skill = Skill.READING,
    average_accuracy: float = 0.7,
    average_confidence: float | None = None,
    hard_item_rate: float | None = None,
    accuracy_trend: float | None = None,
) -> HistoricalSkillProfile:
    return HistoricalSkillProfile(
        skill_snapshot_id=identifier,
        profile_snapshot_id=identifier,
        calculated_at=NOW + timedelta(days=identifier),
        skill=skill,
        score=score,
        evidence_status=EvidenceStatus.ESTABLISHED,
        sample_count=identifier + 1,
        average_accuracy=average_accuracy,
        average_confidence=average_confidence,
        average_difficulty=None,
        hard_item_rate=hard_item_rate,
        accuracy_trend=accuracy_trend,
    )
