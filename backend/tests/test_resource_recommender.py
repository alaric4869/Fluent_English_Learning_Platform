from datetime import date, datetime, timedelta, timezone

from app.domain.learning_evidence.entities import Skill
from app.domain.resources.entities import ResourceCandidate
from app.domain.resources.rule_based_recommender import RuleBasedResourceRecommender
from app.domain.weakness_detection.entities import SkillClassification


NOW = datetime(2026, 9, 13, 10, tzinfo=timezone.utc)


def test_unused_resource_is_preferred_to_recently_studied_material() -> None:
    recommender = RuleBasedResourceRecommender()

    result = recommender.recommend(
        Skill.LISTENING,
        SkillClassification.STABLE,
        [
            _candidate(1, last_studied_at=NOW - timedelta(days=1)),
            _candidate(2),
        ],
        NOW.date(),
    )

    assert result[0].resource_id == 2
    assert any("尚未学习" in reason for reason in result[0].reasons)


def test_weak_skill_prefers_a_slightly_easier_resource() -> None:
    recommender = RuleBasedResourceRecommender()

    result = recommender.recommend(
        Skill.LISTENING,
        SkillClassification.WEAK,
        [
            _candidate(1, difficulty="upper-intermediate"),
            _candidate(2, difficulty="lower-intermediate"),
        ],
        NOW.date(),
    )

    assert result[0].resource_id == 2


def test_resource_assigned_yesterday_is_rotated_even_if_not_completed() -> None:
    result = RuleBasedResourceRecommender().recommend(
        Skill.LISTENING,
        SkillClassification.STABLE,
        [
            _candidate(1, last_assigned_date=NOW.date() - timedelta(days=1)),
            _candidate(2),
        ],
        NOW.date(),
    )

    assert result[0].resource_id == 2


def test_candidates_for_another_skill_are_not_returned() -> None:
    result = RuleBasedResourceRecommender().recommend(
        Skill.LISTENING,
        SkillClassification.STABLE,
        [_candidate(1, skill=Skill.READING)],
        NOW.date(),
    )

    assert result == ()


def _candidate(
    identifier: int,
    *,
    skill: Skill = Skill.LISTENING,
    difficulty: str = "intermediate",
    last_studied_at: datetime | None = None,
    last_assigned_date: date | None = None,
) -> ResourceCandidate:
    return ResourceCandidate(
        id=identifier,
        slug=f"resource-{identifier}",
        title=f"Resource {identifier}",
        resource_type="practice",
        skill=skill,
        topic="Daily English",
        difficulty=difficulty,
        estimated_duration_minutes=30,
        priority=50,
        tags=("test",),
        last_studied_at=last_studied_at,
        last_assigned_date=last_assigned_date,
        completed_session_count=1 if last_studied_at else 0,
    )
