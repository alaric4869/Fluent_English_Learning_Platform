from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.ielts.entities import GradeResult
from app.models.ielts import PracticeAttempt, PracticeSection, PracticeSet


class SqlAlchemyIeltsPracticeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_practice_sets(self) -> list[dict]:
        statement = select(PracticeSet).options(selectinload(PracticeSet.sections)).order_by(
            PracticeSet.skill, PracticeSet.test_number
        )
        return [self._serialize_set(item, include_questions=False) for item in self.session.scalars(statement)]

    def get_practice_set(self, slug: str) -> dict | None:
        statement = (
            select(PracticeSet)
            .where(PracticeSet.slug == slug)
            .options(selectinload(PracticeSet.sections).selectinload(PracticeSection.questions))
        )
        item = self.session.scalar(statement)
        return self._serialize_set(item, include_questions=True) if item else None

    def get_or_create_attempt(self, practice_set_id: int, user_key: str) -> dict:
        statement = select(PracticeAttempt).where(
            PracticeAttempt.practice_set_id == practice_set_id,
            PracticeAttempt.user_key == user_key,
        )
        attempt = self.session.scalar(statement)
        if attempt is None:
            attempt = PracticeAttempt(practice_set_id=practice_set_id, user_key=user_key)
            self.session.add(attempt)
            self.session.commit()
            self.session.refresh(attempt)
        return self._serialize_attempt(attempt)

    def get_attempt(self, attempt_id: int) -> dict | None:
        attempt = self.session.get(PracticeAttempt, attempt_id)
        return self._serialize_attempt(attempt) if attempt else None

    def save_answer(self, attempt_id: int, question_number: int, answer: str) -> dict:
        attempt = self.session.get(PracticeAttempt, attempt_id)
        if attempt is None:
            raise LookupError("Attempt not found")
        updated_answers = dict(attempt.answers)
        updated_answers[str(question_number)] = answer.strip()
        attempt.answers = updated_answers
        attempt.status = "in_progress"
        attempt.results = []
        attempt.score = None
        attempt.submitted_at = None
        self.session.commit()
        self.session.refresh(attempt)
        return self._serialize_attempt(attempt)

    def submit_attempt(self, attempt_id: int, grade: GradeResult) -> dict:
        attempt = self.session.get(PracticeAttempt, attempt_id)
        if attempt is None:
            raise LookupError("Attempt not found")
        attempt.status = "submitted"
        attempt.score = grade.score
        attempt.results = [
            {
                "number": item.number,
                "submitted_answer": item.submitted_answer,
                "correct_answers": list(item.correct_answers),
                "is_correct": item.is_correct,
                "explanation": item.explanation,
            }
            for item in grade.questions
        ]
        attempt.submitted_at = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(attempt)
        return self._serialize_attempt(attempt)

    @staticmethod
    def _serialize_set(item: PracticeSet, include_questions: bool) -> dict:
        sections = []
        for section in item.sections:
            serialized = {
                "id": section.id,
                "order_index": section.order_index,
                "title": section.title,
                "instructions": section.instructions,
                "content_blocks": section.content_blocks,
                "has_audio": bool(section.audio_path),
                "audio_path": section.audio_path,
            }
            if include_questions:
                serialized["questions"] = [
                    {
                        "number": question.number,
                        "prompt": question.prompt,
                        "question_type": question.question_type,
                        "options": question.options,
                        "accepted_answers": question.accepted_answers,
                        "answer_group": question.answer_group,
                        "explanation": question.explanation,
                    }
                    for question in section.questions
                ]
            sections.append(serialized)
        return {
            "id": item.id,
            "slug": item.slug,
            "book_number": item.book_number,
            "test_number": item.test_number,
            "skill": item.skill,
            "title": item.title,
            "description": item.description,
            "duration_minutes": item.duration_minutes,
            "sections": sections,
        }

    @staticmethod
    def _serialize_attempt(attempt: PracticeAttempt) -> dict:
        return {
            "id": attempt.id,
            "practice_set_id": attempt.practice_set_id,
            "status": attempt.status,
            "answers": dict(attempt.answers),
            "results": list(attempt.results),
            "score": attempt.score,
        }
