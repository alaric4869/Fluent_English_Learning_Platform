from datetime import date

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.composition import build_application_services
from app.database import Base
from app.domain.review.entities import ReviewConflictError, ReviewRating
from app.domain.vocabulary.entities import (
    DuplicateVocabularyError,
    MasteryStatus,
    VocabularyDifficulty,
    VocabularyDraft,
)
from app.models.vocabulary import ReviewAttemptModel


TODAY = date(2026, 9, 13)


def test_new_chunk_becomes_due_and_review_requests_are_idempotent() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        services = build_application_services(session)
        item = services.vocabulary.add_item(
            "learner",
            _draft("make an appointment", learned_on=date(2026, 9, 12)),
            TODAY,
        )

        assert item.mastery_status is MasteryStatus.NEW
        assert item.next_review_date == TODAY
        assert services.review.get_due_count("learner", TODAY) == 1
        assert services.review.get_due_reviews("learner", TODAY)[0].id == item.id

        request_id = "d0f5f390-2c22-46c4-850b-ea89b5c8d6a8"
        first = services.review.record_review(
            "learner",
            item.review_item_id,
            ReviewRating.GOOD,
            TODAY,
            request_id,
        )
        repeated = services.review.record_review(
            "learner",
            item.review_item_id,
            ReviewRating.GOOD,
            TODAY,
            request_id,
        )

        assert first.created is True
        assert repeated.created is False
        assert repeated.review_attempt_id == first.review_attempt_id
        assert first.next_review_date == date(2026, 9, 15)
        assert first.review_count == 1
        assert services.review.get_due_count("learner", TODAY) == 0
        assert session.scalar(select(func.count()).select_from(ReviewAttemptModel)) == 1


def test_reused_request_id_with_another_rating_is_rejected() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        services = build_application_services(session)
        item = services.vocabulary.add_item(
            "learner",
            _draft("reschedule my appointment", learned_on=date(2026, 9, 12)),
            TODAY,
        )
        request_id = "7a3cecb4-4581-4e77-9815-7033d9986b0e"
        services.review.record_review(
            "learner",
            item.review_item_id,
            ReviewRating.GOOD,
            TODAY,
            request_id,
        )

        with pytest.raises(ReviewConflictError):
            services.review.record_review(
                "learner",
                item.review_item_id,
                ReviewRating.AGAIN,
                TODAY,
                request_id,
            )


def test_library_normalizes_duplicates_and_filters_content() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        services = build_application_services(session)
        services.vocabulary.add_item(
            "learner",
            _draft("Make an Appointment", learned_on=TODAY),
            TODAY,
        )
        services.vocabulary.add_item(
            "learner",
            _draft(
                "pick up a prescription",
                learned_on=TODAY,
                difficulty=VocabularyDifficulty.HARD,
                meaning="领取处方药",
            ),
            TODAY,
        )

        with pytest.raises(DuplicateVocabularyError):
            services.vocabulary.add_item(
                "learner",
                _draft("  make   an appointment  ", learned_on=TODAY),
                TODAY,
            )

        filtered = services.vocabulary.get_library(
            "learner",
            search="处方",
            difficulty=VocabularyDifficulty.HARD,
        )

        assert filtered.total_count == 2
        assert filtered.mastered_count == 0
        assert [item.chunk for item in filtered.items] == ["pick up a prescription"]


def _draft(
    chunk: str,
    *,
    learned_on: date,
    difficulty: VocabularyDifficulty = VocabularyDifficulty.MEDIUM,
    meaning: str = "预约",
) -> VocabularyDraft:
    return VocabularyDraft(
        chunk=chunk,
        meaning=meaning,
        example_sentence="I need to make an appointment tomorrow.",
        learned_on=learned_on,
        personal_note="Useful in Australia",
        difficulty=difficulty,
        source_resource_id=None,
        source_context="Daily English",
        tags=("appointments", "Daily Life", "appointments"),
    )
