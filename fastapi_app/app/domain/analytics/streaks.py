from datetime import date, timedelta


def calculate_streaks(
    activity_dates: tuple[date, ...],
    today: date,
) -> tuple[int, int]:
    ordered = sorted({value for value in activity_dates if value <= today})
    if not ordered:
        return 0, 0

    longest = 1
    running = 1
    for previous, current in zip(ordered, ordered[1:]):
        if current == previous + timedelta(days=1):
            running += 1
            longest = max(longest, running)
        else:
            running = 1

    latest = ordered[-1]
    if latest < today - timedelta(days=1):
        return 0, longest

    current_streak = 1
    for index in range(len(ordered) - 1, 0, -1):
        if ordered[index] != ordered[index - 1] + timedelta(days=1):
            break
        current_streak += 1
    return current_streak, longest
