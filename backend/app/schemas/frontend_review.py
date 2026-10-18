from datetime import date, datetime

from pydantic import BaseModel


class DueReviewItemResponse(BaseModel):
    review_item_id: int
    target_type: str
    target_id: int
    title: str
    secondary_text: str
    answer_label: str
    answer: str
    note: str
    target_label: str
    mastery_status: str
    source_title: str
    due_label: str
    next_review_date: date
    review_count: int


class VocabularyLibraryItemResponse(BaseModel):
    id: int
    chunk: str
    meaning: str
    example_sentence: str
    learned_on: date
    personal_note: str
    difficulty: str
    mastery_status: str
    source_title: str
    source_context: str
    tags: list[str]
    favorite: bool
    saved_for_later: bool
    review_item_id: int
    review_step: int
    next_review_date: date
    last_reviewed_at: datetime | None
    review_count: int


class ReviewWorkspaceResponse(BaseModel):
    today: date
    due_count: int
    total_count: int
    mastered_count: int
    due_items: list[DueReviewItemResponse]
    library_items: list[VocabularyLibraryItemResponse]
