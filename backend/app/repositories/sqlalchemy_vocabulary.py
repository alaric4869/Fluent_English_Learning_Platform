from datetime import date, datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.domain.review.entities import ReviewScheduleState
from app.domain.vocabulary.entities import (
    DuplicateVocabularyError,
    MasteryStatus,
    VocabularyDifficulty,
    VocabularyDraft,
    VocabularyItem,
)
from app.models.vocabulary import ReviewItemModel, VocabularyItemModel


class SqlAlchemyVocabularyRepository:
    def __init__(self, session: Session, scheduler_version: str) -> None:
        self.session = session
        self.scheduler_version = scheduler_version

    def create(
        self,
        user_key: str,
        normalized_chunk: str,
        draft: VocabularyDraft,
        initial_schedule: ReviewScheduleState,
    ) -> VocabularyItem:
        vocabulary = VocabularyItemModel(
            user_key=user_key,
            chunk=draft.chunk,
            normalized_chunk=normalized_chunk,
            meaning=draft.meaning,
            example_sentence=draft.example_sentence,
            learned_on=draft.learned_on,
            personal_note=draft.personal_note,
            difficulty=draft.difficulty.value,
            source_resource_id=draft.source_resource_id,
            source_context=draft.source_context,
            tags=list(draft.tags),
            favorite=False,
            saved_for_later=False,
        )
        review = ReviewItemModel(
            user_key=user_key,
            item_type="vocabulary",
            scheduler_version=self.scheduler_version,
            schedule_step=initial_schedule.step,
            next_review_date=initial_schedule.next_review_date,
            mastery_status=initial_schedule.mastery_status.value,
            review_count=0,
            active=True,
        )
        vocabulary.review_item = review
        self.session.add(vocabulary)
        try:
            self.session.commit()
        except IntegrityError as error:
            self.session.rollback()
            raise DuplicateVocabularyError(
                "This vocabulary chunk already exists"
            ) from error
        saved = self._get(vocabulary.id)
        return to_vocabulary_item(saved)

    def find_by_normalized_chunk(
        self,
        user_key: str,
        normalized_chunk: str,
    ) -> VocabularyItem | None:
        statement = (
            select(VocabularyItemModel)
            .where(
                VocabularyItemModel.user_key == user_key,
                VocabularyItemModel.normalized_chunk == normalized_chunk,
            )
            .options(selectinload(VocabularyItemModel.review_item))
        )
        item = self.session.scalar(statement)
        return to_vocabulary_item(item) if item else None

    def get(self, user_key: str, vocabulary_item_id: int) -> VocabularyItem | None:
        statement = (
            select(VocabularyItemModel)
            .where(
                VocabularyItemModel.id == vocabulary_item_id,
                VocabularyItemModel.user_key == user_key,
            )
            .options(selectinload(VocabularyItemModel.review_item))
        )
        item = self.session.scalar(statement)
        return to_vocabulary_item(item) if item else None

    def list_items(
        self,
        user_key: str,
        search: str,
        mastery_status: MasteryStatus | None,
        difficulty: VocabularyDifficulty | None,
        limit: int,
    ) -> tuple[VocabularyItem, ...]:
        statement = (
            select(VocabularyItemModel)
            .join(
                ReviewItemModel,
                ReviewItemModel.vocabulary_item_id == VocabularyItemModel.id,
            )
            .where(VocabularyItemModel.user_key == user_key)
            .options(selectinload(VocabularyItemModel.review_item))
        )
        if search:
            pattern = f"%{search.casefold()}%"
            statement = statement.where(
                or_(
                    func.lower(VocabularyItemModel.chunk).like(pattern),
                    func.lower(VocabularyItemModel.meaning).like(pattern),
                    func.lower(VocabularyItemModel.example_sentence).like(pattern),
                    func.lower(VocabularyItemModel.source_context).like(pattern),
                )
            )
        if mastery_status is not None:
            statement = statement.where(
                ReviewItemModel.mastery_status == mastery_status.value
            )
        if difficulty is not None:
            statement = statement.where(
                VocabularyItemModel.difficulty == difficulty.value
            )
        statement = statement.order_by(
            VocabularyItemModel.learned_on.desc(),
            VocabularyItemModel.id.desc(),
        ).limit(limit)
        return tuple(
            to_vocabulary_item(item) for item in self.session.scalars(statement)
        )

    def count_items(
        self,
        user_key: str,
        mastery_status: MasteryStatus | None = None,
    ) -> int:
        statement = (
            select(func.count())
            .select_from(VocabularyItemModel)
            .join(
                ReviewItemModel,
                ReviewItemModel.vocabulary_item_id == VocabularyItemModel.id,
            )
            .where(VocabularyItemModel.user_key == user_key)
        )
        if mastery_status is not None:
            statement = statement.where(
                ReviewItemModel.mastery_status == mastery_status.value
            )
        return self.session.scalar(statement) or 0

    def count_learned_between(
        self,
        user_key: str,
        start_date: date,
        end_date: date,
    ) -> int:
        statement = select(func.count()).select_from(VocabularyItemModel).where(
            VocabularyItemModel.user_key == user_key,
            VocabularyItemModel.learned_on >= start_date,
            VocabularyItemModel.learned_on < end_date,
        )
        return self.session.scalar(statement) or 0

    def _get(self, vocabulary_item_id: int) -> VocabularyItemModel:
        statement = (
            select(VocabularyItemModel)
            .where(VocabularyItemModel.id == vocabulary_item_id)
            .options(selectinload(VocabularyItemModel.review_item))
        )
        return self.session.scalars(statement).one()



def to_vocabulary_item(item: VocabularyItemModel) -> VocabularyItem:
    review = item.review_item
    return VocabularyItem(
        id=item.id,
        user_key=item.user_key,
        chunk=item.chunk,
        meaning=item.meaning,
        example_sentence=item.example_sentence,
        learned_on=item.learned_on,
        personal_note=item.personal_note,
        difficulty=VocabularyDifficulty(item.difficulty),
        mastery_status=MasteryStatus(review.mastery_status),
        source_resource_id=item.source_resource_id,
        source_context=item.source_context,
        tags=tuple(item.tags),
        favorite=item.favorite,
        saved_for_later=item.saved_for_later,
        review_item_id=review.id,
        review_step=review.schedule_step,
        next_review_date=review.next_review_date,
        last_reviewed_at=_as_utc(review.last_reviewed_at),
        review_count=review.review_count,
        created_at=_as_utc(item.created_at),
        updated_at=_as_utc(item.updated_at),
    )


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
