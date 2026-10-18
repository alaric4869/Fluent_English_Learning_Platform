from datetime import date

from app.domain.analytics.streaks import calculate_streaks


def test_streaks_count_consecutive_activity_through_today() -> None:
    current, longest = calculate_streaks(
        (
            date(2026, 9, 1),
            date(2026, 9, 2),
            date(2026, 9, 10),
            date(2026, 9, 11),
            date(2026, 9, 12),
            date(2026, 9, 13),
        ),
        date(2026, 9, 13),
    )

    assert current == 4
    assert longest == 4


def test_current_streak_allows_today_to_be_unfinished_but_not_a_long_gap() -> None:
    assert calculate_streaks(
        (date(2026, 9, 10), date(2026, 9, 11), date(2026, 9, 12)),
        date(2026, 9, 13),
    ) == (3, 3)
    assert calculate_streaks(
        (date(2026, 9, 10), date(2026, 9, 11)),
        date(2026, 9, 13),
    ) == (0, 2)


def test_streaks_ignore_duplicates_and_future_dates() -> None:
    assert calculate_streaks(
        (date(2026, 9, 13), date(2026, 9, 13), date(2026, 9, 14)),
        date(2026, 9, 13),
    ) == (1, 1)
