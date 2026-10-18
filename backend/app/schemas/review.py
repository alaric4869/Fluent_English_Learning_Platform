from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.review.entities import ReviewRating, ReviewTargetType
from app.domain.vocabulary.entities import MasteryStatus, VocabularyDifficulty


class VocabularyCreateRequest(BaseModel):
    chunk: str = Field(min_length=1, max_length=300)
    meaning: str = Field(min_length=1, max_length=2000)
    example_sentence: str = Field(default="", max_length=2000)
    learned_on: date | None = None
    personal_note: str = Field(default="", max_length=2000)
    difficulty: VocabularyDifficulty = VocabularyDifficulty.MEDIUM
    source_resource_id: int | None = None
    source_context: str = Field(default="", max_length=1000)
    tags: list[str] = Field(default_factory=list, max_length=20)


class VocabularyItemResponse(BaseModel):
    id: int
    chunk: str
    meaning: str
    example_sentence: str
    learned_on: date
    difficulty: VocabularyDifficulty
    mastery_status: MasteryStatus
    review_item_id: int
    review_step: int
    next_review_date: date
    review_count: int


class ReviewRatingRequest(BaseModel):
    rating: ReviewRating
    request_id: UUID


class RecordedReviewResponse(BaseModel):
    review_attempt_id: int
    target_type: ReviewTargetType
    target_id: int
    vocabulary_item_id: int | None
    saved_sentence_id: int | None
    review_item_id: int
    mastery_status: MasteryStatus
    next_review_date: date
    review_count: int
    created: bool
