from datetime import date

from app.domain.review.entities import ReviewRating
from app.domain.review.fixed_interval_scheduler import FixedIntervalReviewScheduler
from app.domain.vocabulary.entities import MasteryStatus


LEARNED_ON = date(2026, 9, 1)


def test_good_ratings_follow_day_1_3_7_14_30_schedule() -> None:
    scheduler = FixedIntervalReviewScheduler()
    state = scheduler.initial_state(LEARNED_ON)

    assert state.next_review_date == date(2026, 9, 2)
    assert state.mastery_status is MasteryStatus.NEW

    expected_dates = (
        date(2026, 9, 4),
        date(2026, 9, 8),
        date(2026, 9, 15),
        date(2026, 10, 1),
    )
    for expected in expected_dates:
        result = scheduler.schedule(
            state,
            ReviewRating.GOOD,
            state.next_review_date,
        )
        state = result.state
        assert state.next_review_date == expected

    assert state.mastery_status is MasteryStatus.FAMILIAR

    final = scheduler.schedule(state, ReviewRating.GOOD, state.next_review_date)

    assert final.state.mastery_status is MasteryStatus.MASTERED
    assert final.state.next_review_date == date(2026, 10, 31)


def test_again_hard_and_easy_have_explainable_effects() -> None:
    scheduler = FixedIntervalReviewScheduler()
    initial = scheduler.initial_state(LEARNED_ON)
    after_first = scheduler.schedule(
        initial,
        ReviewRating.GOOD,
        initial.next_review_date,
    ).state
    familiar = scheduler.schedule(
        after_first,
        ReviewRating.GOOD,
        after_first.next_review_date,
    ).state

    again = scheduler.schedule(familiar, ReviewRating.AGAIN, date(2026, 9, 8))
    hard = scheduler.schedule(familiar, ReviewRating.HARD, date(2026, 9, 8))
    easy = scheduler.schedule(initial, ReviewRating.EASY, initial.next_review_date)

    assert again.state.step == 0
    assert again.state.mastery_status is MasteryStatus.LEARNING
    assert again.state.next_review_date == date(2026, 9, 9)
    assert hard.state.step == familiar.step
    assert hard.interval_days == 2
    assert easy.state.step == 2
    assert easy.state.mastery_status is MasteryStatus.FAMILIAR
    assert easy.interval_days == 4
