from datetime import date, datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.domain.listening.entities import (
    ListeningSentenceDraft,
    ListeningSentenceStatus,
    SavedListeningSentence,
)
from app.domain.review.entities import ReviewScheduleState
from app.domain.vocabulary.entities import MasteryStatus
from app.models.practice_notes import SavedSentenceModel
from app.models.vocabulary import ReviewItemModel


class SqlAlchemyListeningSentenceRepository:
    def __init__(self, session: Session, scheduler_version: str) -> None:
        self.session = session
        self.scheduler_version = scheduler_version

    def create(
        self,
        user_key: str,
        draft: ListeningSentenceDraft,
        initial_schedule: ReviewScheduleState | None,
    ) -> SavedListeningSentence:
        item = SavedSentenceModel(
            user_key=user_key,
            sentence=draft.sentence,
            meaning=draft.meaning,
            learned_on=draft.learned_on,
            practice_status=draft.practice_status.value,
            note=draft.note,
            source_resource_id=draft.source_resource_id,
            source_context=draft.source_context,
            favorite=False,
            saved_for_later=False,
        )
        if initial_schedule is not None:
            item.review_item = ReviewItemModel(
                user_key=user_key,
                item_type="saved_sentence",
                scheduler_version=self.scheduler_version,
                schedule_step=initial_schedule.step,
                next_review_date=initial_schedule.next_review_date,
                mastery_status=initial_schedule.mastery_status.value,
                review_count=0,
                active=True,
            )
        self.session.add(item)
        self.session.commit()
        return self._get(item.id)

    def get(self, user_key: str, sentence_id: int) -> SavedListeningSentence | None:
        statement = (
            select(SavedSentenceModel)
            .where(
                SavedSentenceModel.id == sentence_id,
                SavedSentenceModel.user_key == user_key,
            )
            .options(selectinload(SavedSentenceModel.review_item))
        )
        item = self.session.scalar(statement)
        return to_saved_sentence(item) if item else None

    def list_items(
        self,
        user_key: str,
        search: str,
        status: ListeningSentenceStatus | None,
        limit: int,
    ) -> tuple[SavedListeningSentence, ...]:
        statement = (
            select(SavedSentenceModel)
            .where(SavedSentenceModel.user_key == user_key)
            .options(selectinload(SavedSentenceModel.review_item))
        )
        if search:
            pattern = f"%{search.casefold()}%"
            statement = statement.where(
                or_(
                    func.lower(SavedSentenceModel.sentence).like(pattern),
                    func.lower(SavedSentenceModel.meaning).like(pattern),
                    func.lower(SavedSentenceModel.note).like(pattern),
                    func.lower(SavedSentenceModel.source_context).like(pattern),
                )
            )
        if status is not None:
            statement = statement.where(
                SavedSentenceModel.practice_status == status.value
            )
        statement = statement.order_by(
            SavedSentenceModel.created_at.desc(), SavedSentenceModel.id.desc()
        ).limit(limit)
        return tuple(to_saved_sentence(item) for item in self.session.scalars(statement))

    def update_status(
        self,
        user_key: str,
        sentence_id: int,
        status: ListeningSentenceStatus,
    ) -> SavedListeningSentence | None:
        item = self.session.scalar(
            select(SavedSentenceModel).where(
                SavedSentenceModel.id == sentence_id,
                SavedSentenceModel.user_key == user_key,
            )
        )
        if item is None:
            return None
        item.practice_status = status.value
        self.session.commit()
        return self._get(item.id)

    def count_learned_between(
        self,
        user_key: str,
        start_date: date,
        end_date: date,
    ) -> int:
        statement = select(func.count()).select_from(SavedSentenceModel).where(
            SavedSentenceModel.user_key == user_key,
            SavedSentenceModel.learned_on >= start_date,
            SavedSentenceModel.learned_on < end_date,
        )
        return self.session.scalar(statement) or 0

    def _get(self, sentence_id: int) -> SavedListeningSentence:
        item = self.session.scalar(
            select(SavedSentenceModel)
            .where(SavedSentenceModel.id == sentence_id)
            .options(selectinload(SavedSentenceModel.review_item))
        )
        if item is None:
            raise LookupError("Saved sentence not found")
        return to_saved_sentence(item)


def to_saved_sentence(item: SavedSentenceModel) -> SavedListeningSentence:
    review = item.review_item
    return SavedListeningSentence(
        id=item.id,
        user_key=item.user_key,
        sentence=item.sentence,
        meaning=item.meaning,
        learned_on=item.learned_on,
        practice_status=ListeningSentenceStatus(item.practice_status),
        note=item.note,
        source_resource_id=item.source_resource_id,
        source_context=item.source_context,
        favorite=item.favorite,
        saved_for_later=item.saved_for_later,
        review_item_id=review.id if review else None,
        review_step=review.schedule_step if review else None,
        next_review_date=review.next_review_date if review else None,
        last_reviewed_at=_as_utc(review.last_reviewed_at) if review else None,
        review_count=review.review_count if review else 0,
        mastery_status=MasteryStatus(review.mastery_status) if review else None,
        created_at=_as_utc(item.created_at),
        updated_at=_as_utc(item.updated_at),
    )


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
