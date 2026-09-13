from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.review.entities import (
    RecordReviewCommand,
    RecordedReview,
    ReviewConflictError,
    ReviewQueueItem,
    ReviewScheduleState,
    ReviewTargetType,
)
from app.domain.vocabulary.entities import MasteryStatus
from app.models.vocabulary import ReviewAttemptModel, ReviewItemModel


class SqlAlchemyReviewRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_due(
        self,
        user_key: str,
        due_on: date,
        limit: int,
    ) -> tuple[ReviewQueueItem, ...]:
        statement = (
            select(ReviewItemModel)
            .where(
                ReviewItemModel.user_key == user_key,
                ReviewItemModel.active.is_(True),
                ReviewItemModel.next_review_date <= due_on,
            )
            .order_by(ReviewItemModel.next_review_date, ReviewItemModel.id)
            .limit(limit)
        )
        return tuple(self._to_queue_item(item) for item in self.session.scalars(statement))

    def count_due(self, user_key: str, due_on: date) -> int:
        statement = select(func.count()).select_from(ReviewItemModel).where(
            ReviewItemModel.user_key == user_key,
            ReviewItemModel.active.is_(True),
            ReviewItemModel.next_review_date <= due_on,
        )
        return self.session.scalar(statement) or 0

    def count_attempts_through(self, user_key: str, through: datetime) -> int:
        statement = (
            select(func.count())
            .select_from(ReviewAttemptModel)
            .join(
                ReviewItemModel,
                ReviewItemModel.id == ReviewAttemptModel.review_item_id,
            )
            .where(
                ReviewItemModel.user_key == user_key,
                ReviewAttemptModel.reviewed_at < through,
            )
        )
        return self.session.scalar(statement) or 0

    def get_item(self, user_key: str, review_item_id: int) -> ReviewQueueItem | None:
        statement = (
            select(ReviewItemModel)
            .where(
                ReviewItemModel.id == review_item_id,
                ReviewItemModel.user_key == user_key,
                ReviewItemModel.active.is_(True),
            )
        )
        item = self.session.scalar(statement)
        return self._to_queue_item(item) if item else None

    def record(self, command: RecordReviewCommand) -> RecordedReview:
        existing_attempt = self.session.scalar(
            select(ReviewAttemptModel).where(
                ReviewAttemptModel.request_id == command.request_id
            )
        )
        if existing_attempt is not None:
            if existing_attempt.review_item_id != command.review_item_id:
                raise ReviewConflictError("Review request ID was already used")
            if existing_attempt.rating != command.rating.value:
                raise ReviewConflictError(
                    "Review request ID was already used with another rating"
                )
            item = self._get(command.user_key, command.review_item_id)
            return self._to_recorded(existing_attempt.id, item, created=False)

        item = self._get(command.user_key, command.review_item_id)
        stored_state = ReviewScheduleState(
            step=item.schedule_step,
            next_review_date=item.next_review_date,
            mastery_status=MasteryStatus(item.mastery_status),
        )
        if stored_state != command.previous_state:
            raise ReviewConflictError("Review state changed before it could be saved")

        next_state = command.result.state
        item.schedule_step = next_state.step
        item.next_review_date = next_state.next_review_date
        item.last_reviewed_at = command.reviewed_at
        item.review_count += 1
        item.mastery_status = next_state.mastery_status.value
        attempt = ReviewAttemptModel(
            review_item_id=item.id,
            request_id=command.request_id,
            rating=command.rating.value,
            previous_step=command.previous_state.step,
            next_step=next_state.step,
            previous_review_date=command.previous_state.next_review_date,
            next_review_date=next_state.next_review_date,
            interval_days=command.result.interval_days,
            previous_mastery_status=command.previous_state.mastery_status.value,
            new_mastery_status=next_state.mastery_status.value,
            reviewed_at=command.reviewed_at,
        )
        self.session.add(attempt)
        self.session.commit()
        self.session.refresh(attempt)
        saved = self._get(command.user_key, command.review_item_id)
        return self._to_recorded(attempt.id, saved, created=True)

    def _get(self, user_key: str, review_item_id: int) -> ReviewItemModel:
        statement = (
            select(ReviewItemModel)
            .where(
                ReviewItemModel.id == review_item_id,
                ReviewItemModel.user_key == user_key,
                ReviewItemModel.active.is_(True),
            )
        )
        item = self.session.scalar(statement)
        if item is None:
            raise LookupError("Review item not found")
        return item

    @staticmethod
    def _to_recorded(
        attempt_id: int,
        item: ReviewItemModel,
        *,
        created: bool,
    ) -> RecordedReview:
        return RecordedReview(
            review_attempt_id=attempt_id,
            target_type=ReviewTargetType(item.item_type),
            target_id=SqlAlchemyReviewRepository._target_id(item),
            vocabulary_item_id=item.vocabulary_item_id,
            saved_sentence_id=item.saved_sentence_id,
            review_item_id=item.id,
            mastery_status=MasteryStatus(item.mastery_status),
            next_review_date=item.next_review_date,
            review_count=item.review_count,
            created=created,
        )

    @staticmethod
    def _to_queue_item(item: ReviewItemModel) -> ReviewQueueItem:
        return ReviewQueueItem(
            review_item_id=item.id,
            user_key=item.user_key,
            target_type=ReviewTargetType(item.item_type),
            target_id=SqlAlchemyReviewRepository._target_id(item),
            scheduler_version=item.scheduler_version,
            review_step=item.schedule_step,
            next_review_date=item.next_review_date,
            last_reviewed_at=_as_utc(item.last_reviewed_at),
            review_count=item.review_count,
            mastery_status=MasteryStatus(item.mastery_status),
        )

    @staticmethod
    def _target_id(item: ReviewItemModel) -> int:
        target_id = item.vocabulary_item_id or item.saved_sentence_id
        if target_id is None:
            raise RuntimeError(f"Review item {item.id} has no target")
        return target_id


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
