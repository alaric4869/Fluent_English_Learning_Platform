from datetime import datetime, timedelta, timezone

from app.domain.learning_evidence.entities import HistoricalSkillPerformance, Skill
from app.domain.learner_profile.entities import EvidenceStatus
from app.domain.learner_profile.rule_based_evaluator import RuleBasedSkillEvaluator


NOW = datetime(2026, 9, 13, tzinfo=timezone.utc)


def test_skill_without_history_is_explicitly_unscored() -> None:
    result = RuleBasedSkillEvaluator().evaluate(Skill.SPEAKING, [])

    assert result.score is None
    assert result.evidence_status is EvidenceStatus.NO_DATA
    assert result.sample_count == 0
    assert result.calculation_weights == {}


def test_one_accuracy_sample_is_a_provisional_score() -> None:
    result = RuleBasedSkillEvaluator().evaluate(
        Skill.LISTENING,
        [_performance(1, accuracy=0.60, skill=Skill.LISTENING)],
    )

    assert result.score == 60.0
    assert result.evidence_status is EvidenceStatus.PROVISIONAL
    assert result.calculation_weights == {"accuracy": 1.0}
    assert "至少需要 2 次数据" in result.explanation


def test_established_score_uses_available_signals_and_calculates_trend() -> None:
    history = [
        _performance(1, accuracy=0.50, confidence=4, hard_item_count=2),
        _performance(2, accuracy=0.60, confidence=4, hard_item_count=2),
        _performance(3, accuracy=0.70, confidence=4, hard_item_count=2),
        _performance(4, accuracy=0.80, confidence=4, hard_item_count=2),
    ]

    result = RuleBasedSkillEvaluator().evaluate(Skill.READING, history)

    assert result.score == 68.8
    assert result.evidence_status is EvidenceStatus.ESTABLISHED
    assert result.average_accuracy == 0.65
    assert result.average_confidence == 4
    assert result.hard_item_rate == 0.2
    assert result.accuracy_trend == 0.2
    assert result.evidence_ids == (1, 2, 3, 4)
    assert result.calculation_weights == {
        "accuracy": 0.75,
        "confidence": 0.15,
        "hard_item_resilience": 0.10,
    }


def test_only_the_configured_recent_window_affects_the_score() -> None:
    history = [_performance(1, accuracy=0.0)] + [
        _performance(identifier, accuracy=1.0)
        for identifier in range(2, 7)
    ]

    result = RuleBasedSkillEvaluator().evaluate(Skill.READING, history)

    assert result.sample_count == 5
    assert result.score == 100.0
    assert result.evidence_ids == (2, 3, 4, 5, 6)


def _performance(
    identifier: int,
    *,
    accuracy: float,
    confidence: int | None = None,
    hard_item_count: int | None = None,
    skill: Skill = Skill.READING,
) -> HistoricalSkillPerformance:
    return HistoricalSkillPerformance(
        id=identifier,
        study_session_id=identifier,
        user_key="learner",
        skill=skill,
        accuracy=accuracy,
        item_count=10,
        correct_item_count=round(accuracy * 10),
        incorrect_item_count=10 - round(accuracy * 10),
        hard_item_count=hard_item_count,
        confidence=confidence,
        perceived_difficulty=None,
        occurred_at=NOW + timedelta(days=identifier),
        metrics={},
    )
