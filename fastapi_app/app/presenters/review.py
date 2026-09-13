from datetime import date

from app.domain.resources.entities import LearningResourceDetails
from app.domain.listening.entities import SavedListeningSentence
from app.domain.review.entities import ReviewQueueItem, ReviewTargetType
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
    due_items: tuple[ReviewQueueItem, ...],
    vocabulary_targets: dict[int, VocabularyItem],
    sentence_targets: dict[int, SavedListeningSentence],
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
            _present_due_item(
                item,
                today,
                vocabulary_targets,
                sentence_targets,
                resources,
            )
            for item in due_items
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


def _present_due_item(
    queue_item: ReviewQueueItem,
    today: date,
    vocabulary_targets: dict[int, VocabularyItem],
    sentence_targets: dict[int, SavedListeningSentence],
    resources: dict[int, LearningResourceDetails],
) -> dict:
    overdue_days = max(0, (today - queue_item.next_review_date).days)
    if queue_item.target_type is ReviewTargetType.VOCABULARY:
        target = vocabulary_targets[queue_item.target_id]
        source_id = target.source_resource_id
        source_context = target.source_context
        title = target.chunk
        secondary_text = target.example_sentence
        answer_label = "MEANING"
        answer = target.meaning
        note = target.personal_note
        target_label = "词块"
    else:
        target = sentence_targets[queue_item.target_id]
        source_id = target.source_resource_id
        source_context = target.source_context
        title = target.sentence
        secondary_text = "先回想这句话在音频中的声音、连读和重音。"
        answer_label = "MEANING / LISTENING NOTE"
        answer = target.meaning or "未填写中文释义"
        note = target.note
        target_label = "听力难句"
    resource = resources.get(source_id) if source_id else None
    return {
        "review_item": queue_item,
        "title": title,
        "secondary_text": secondary_text,
        "answer_label": answer_label,
        "answer": answer,
        "note": note,
        "target_label": target_label,
        "mastery_label": MASTERY_LABELS[queue_item.mastery_status],
        "source_title": resource.title if resource else source_context or "手动添加",
        "due_label": f"逾期 {overdue_days} 天" if overdue_days else "今天到期",
    }
