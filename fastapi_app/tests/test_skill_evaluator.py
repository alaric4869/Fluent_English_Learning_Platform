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


def test_subjective_session_is_scored_without_inventing_accuracy() -> None:
    result = RuleBasedSkillEvaluator().evaluate(
        Skill.LISTENING,
        [
            _performance(
                1,
                accuracy=None,
                confidence=3,
                perceived_difficulty=4,
                skill=Skill.LISTENING,
            )
        ],
    )

    assert result.score == 52.0
    assert result.average_accuracy is None
    assert result.average_confidence == 3
    assert result.average_difficulty == 4
    assert result.calculation_weights == {
        "self_confidence": 0.6,
        "perceived_ease": 0.4,
    }
    assert "不等同于客观正确率" in result.explanation


def test_unrated_sessions_remain_unscored_and_provisional() -> None:
    result = RuleBasedSkillEvaluator().evaluate(
        Skill.SPEAKING,
        [
            _performance(1, accuracy=None, skill=Skill.SPEAKING),
            _performance(2, accuracy=None, skill=Skill.SPEAKING),
        ],
    )

    assert result.score is None
    assert result.evidence_status is EvidenceStatus.PROVISIONAL
    assert result.sample_count == 2
    assert result.calculation_weights == {}


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
    accuracy: float | None,
    confidence: int | None = None,
    hard_item_count: int | None = None,
    perceived_difficulty: int | None = None,
    skill: Skill = Skill.READING,
) -> HistoricalSkillPerformance:
    return HistoricalSkillPerformance(
        id=identifier,
        study_session_id=identifier,
        user_key="learner",
        skill=skill,
        accuracy=accuracy,
        item_count=10 if accuracy is not None else 0,
        correct_item_count=round(accuracy * 10) if accuracy is not None else 0,
        incorrect_item_count=(10 - round(accuracy * 10)) if accuracy is not None else 0,
        hard_item_count=hard_item_count,
        confidence=confidence,
        perceived_difficulty=perceived_difficulty,
        occurred_at=NOW + timedelta(days=identifier),
        metrics={},
    )
