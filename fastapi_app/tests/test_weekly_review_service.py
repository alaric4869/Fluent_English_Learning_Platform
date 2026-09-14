from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.composition import build_application_services
from app.database import Base
from app.domain.learning_evidence.entities import Skill
from app.domain.listening.entities import (
    ListeningSentenceDraft,
    ListeningSentenceStatus,
)
from app.domain.study_plan.entities import StudyPlanItemStatus
from app.domain.vocabulary.entities import VocabularyDifficulty, VocabularyDraft
from app.domain.weekly_review.calculations import select_skill_highlights, week_range
from app.domain.weekly_review.entities import WeeklySkillSummary
from app.models.learning_evidence import LearningResource, StudySession
from app.models.vocabulary import ReviewAttemptModel


SYDNEY = ZoneInfo("Australia/Sydney")


def test_week_range_uses_monday_to_sunday() -> None:
    assert week_range(date(2026, 9, 20)) == (
        date(2026, 9, 14),
        date(2026, 9, 21),
    )


def test_highlights_require_real_session_accuracy() -> None:
    summaries = (
        _skill_summary(Skill.LISTENING, 0.55),
        _skill_summary(Skill.READING, 0.9),
        _skill_summary(Skill.SPEAKING, None),
        _skill_summary(Skill.VOCABULARY, None),
    )

    assert select_skill_highlights(summaries) == (
        Skill.READING,
        Skill.LISTENING,
    )
    assert select_skill_highlights((_skill_summary(Skill.LISTENING, 0.55),)) == (
        Skill.LISTENING,
        None,
    )


def test_weekly_review_aggregates_persisted_learning_facts() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        resources = _add_resources(session)
        services = build_application_services(session)
        today = date(2026, 9, 20)
        plan = services.study_plan.get_or_create_daily_plan("local-user", today)
        for skill in (Skill.LISTENING, Skill.READING):
            item = next(value for value in plan.items if value.skill is skill)
            services.study_plan.update_item_status(
                "local-user", today, item.id, StudyPlanItemStatus.COMPLETED
            )

        listening_resource = resources[Skill.LISTENING]
        reading_resource = resources[Skill.READING]
        session.add_all(
            [
                _session(
                    listening_resource.id,
                    Skill.LISTENING,
                    "listening-attempt",
                    0.5,
                    4,
                    600,
                ),
                _session(
                    reading_resource.id,
                    Skill.READING,
                    "reading-attempt",
                    0.9,
                    1,
                    900,
                ),
            ]
        )
        session.commit()
        vocabulary = services.vocabulary.add_item(
            "local-user",
            VocabularyDraft(
                chunk="reschedule an appointment",
                meaning="改约",
                example_sentence="Could I reschedule my appointment?",
                learned_on=date(2026, 9, 14),
                personal_note="",
                difficulty=VocabularyDifficulty.MEDIUM,
                source_resource_id=reading_resource.id,
                source_context="Reading Test",
                tags=("appointments",),
            ),
            today,
        )
        services.vocabulary.add_item(
            "local-user",
            VocabularyDraft(
                chunk="get back to someone",
                meaning="稍后回复某人",
                example_sentence="I'll get back to you tomorrow.",
                learned_on=today,
                personal_note="",
                difficulty=VocabularyDifficulty.MEDIUM,
                source_resource_id=None,
                source_context="",
                tags=(),
            ),
            today,
        )
        services.listening.save_sentence(
            "local-user",
            ListeningSentenceDraft(
                sentence="Would you mind saying that again?",
                meaning="可以再说一次吗？",
                learned_on=today,
                practice_status=ListeningSentenceStatus.COULD_NOT_HEAR,
                note="Connected speech",
                source_resource_id=listening_resource.id,
                source_context="Listening Test",
                add_to_review=True,
            ),
            today,
        )
        session.add(
            ReviewAttemptModel(
                review_item_id=vocabulary.review_item_id,
                request_id="00000000-0000-4000-8000-000000000011",
                rating="good",
                previous_step=0,
                next_step=1,
                previous_review_date=date(2026, 9, 15),
                next_review_date=date(2026, 9, 17),
                interval_days=2,
                previous_mastery_status="new",
                new_mastery_status="learning",
                reviewed_at=_sydney_datetime(date(2026, 9, 16), 12),
            )
        )
        session.commit()

        review = services.weekly_review.get_current_week("local-user", today)

        assert review.week_start == date(2026, 9, 14)
        assert review.week_end == date(2026, 9, 20)
        assert review.study_days == 1
        assert review.assigned_modules == 4
        assert review.completed_modules == 2
        assert review.completion_rate == 50.0
        assert review.completed_planned_minutes == 60
        assert review.completed_sessions == 2
        assert review.tracked_seconds == 1500
        assert review.vocabulary_learned == 2
        assert review.difficult_sentences_collected == 1
        assert review.review_attempts.total_count == 1
        assert review.review_attempts.retention_rate == 100.0
        assert review.next_week_review_count == 2
        assert review.strongest_skill is Skill.READING
        assert review.weakest_skill is Skill.LISTENING
        assert any("Listening" in item.title for item in review.recommendations)
        assert any("重做" in item.title for item in review.recommendations)


def _skill_summary(skill: Skill, accuracy: float | None) -> WeeklySkillSummary:
    return WeeklySkillSummary(
        skill=skill,
        completed_modules=0,
        completed_sessions=1 if accuracy is not None else 0,
        average_accuracy=accuracy,
        incorrect_item_count=0,
        tracked_seconds=0,
    )


def _add_resources(session: Session) -> dict[Skill, LearningResource]:
    resources = {
        skill: LearningResource(
            slug=f"{skill.value}-weekly-review",
            title=f"{skill.value.title()} weekly resource",
            resource_type="practice",
            skill=skill.value,
            topic="Daily English",
            difficulty="intermediate",
            estimated_duration_minutes=30,
            content={},
            tags=[],
            priority=50,
            active=True,
        )
        for skill in Skill
    }
    session.add_all(resources.values())
    session.commit()
    return resources


def _session(
    resource_id: int,
    skill: Skill,
    source_id: str,
    accuracy: float,
    incorrect_count: int,
    duration_seconds: int,
) -> StudySession:
    completed_at = _sydney_datetime(date(2026, 9, 20), 10)
    return StudySession(
        user_key="local-user",
        resource_id=resource_id,
        skill=skill.value,
        source_type="weekly-test",
        source_id=source_id,
        source_revision=1,
        status="completed",
        started_at=completed_at,
        completed_at=completed_at,
        actual_duration_seconds=duration_seconds,
        accuracy=accuracy,
        attempt_count=1,
        incorrect_item_count=incorrect_count,
        notes="",
    )


def _sydney_datetime(value: date, hour: int) -> datetime:
    return datetime.combine(value, time(hour), tzinfo=SYDNEY).astimezone(timezone.utc)
