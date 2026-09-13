from datetime import date

from app.domain.resources.entities import LearningResourceDetails
from app.domain.vocabulary.entities import (
    MasteryStatus,
    VocabularyDifficulty,
    VocabularyItem,
    VocabularyLibrary,
)


MASTERY_LABELS = {
    MasteryStatus.NEW: "New",
    MasteryStatus.LEARNING: "Learning",
    MasteryStatus.FAMILIAR: "Familiar",
    MasteryStatus.MASTERED: "Mastered",
}

DIFFICULTY_LABELS = {
    VocabularyDifficulty.EASY: "简单",
    VocabularyDifficulty.MEDIUM: "适中",
    VocabularyDifficulty.HARD: "困难",
}


def present_review_page(
    *,
    view: str,
    today: date,
    due_items: tuple[VocabularyItem, ...],
    due_count: int,
    library: VocabularyLibrary,
    resources: dict[int, LearningResourceDetails],
    search: str,
    mastery_status: MasteryStatus | None,
    difficulty: VocabularyDifficulty | None,
) -> dict:
    return {
        "active_page": "review",
        "view": view,
        "today": today,
        "due_count": due_count,
        "total_count": library.total_count,
        "mastered_count": library.mastered_count,
        "due_items": tuple(
            _present_item(item, today, resources) for item in due_items
        ),
        "library_items": tuple(
            _present_item(item, today, resources) for item in library.items
        ),
        "search": search,
        "selected_mastery": mastery_status.value if mastery_status else "",
        "selected_difficulty": difficulty.value if difficulty else "",
        "mastery_options": tuple(
            (status.value, label) for status, label in MASTERY_LABELS.items()
        ),
        "difficulty_options": tuple(
            (value.value, label) for value, label in DIFFICULTY_LABELS.items()
        ),
    }


def present_vocabulary_response(item: VocabularyItem) -> dict:
    return {
        "id": item.id,
        "chunk": item.chunk,
        "meaning": item.meaning,
        "example_sentence": item.example_sentence,
        "learned_on": item.learned_on,
        "difficulty": item.difficulty,
        "mastery_status": item.mastery_status,
        "review_item_id": item.review_item_id,
        "review_step": item.review_step,
        "next_review_date": item.next_review_date,
        "review_count": item.review_count,
    }


def _present_item(
    item: VocabularyItem,
    today: date,
    resources: dict[int, LearningResourceDetails],
) -> dict:
    resource = resources.get(item.source_resource_id) if item.source_resource_id else None
    overdue_days = max(0, (today - item.next_review_date).days)
    return {
        "item": item,
        "mastery_label": MASTERY_LABELS[item.mastery_status],
        "difficulty_label": DIFFICULTY_LABELS[item.difficulty],
        "source_title": resource.title if resource else item.source_context or "手动添加",
        "overdue_days": overdue_days,
        "due_label": f"逾期 {overdue_days} 天" if overdue_days else "今天到期",
    }
