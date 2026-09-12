from dataclasses import dataclass

from app.domain.ielts.entities import PracticeQuestion, QuestionOption, QuestionType
from app.domain.ielts.grading import grade_answers
from app.domain.ielts.repository import IeltsPracticeRepository


class PracticeSetNotFoundError(LookupError):
    pass


@dataclass(frozen=True)
class IncompleteAttemptError(ValueError):
    missing_questions: tuple[int, ...]


class IeltsPracticeService:
    def __init__(self, repository: IeltsPracticeRepository) -> None:
        self.repository = repository

    def list_practice_sets(self) -> list[dict]:
        return self.repository.list_practice_sets()

    def get_practice_workspace(self, slug: str, user_key: str) -> dict:
        practice_set = self._require_set(slug)
        attempt = self.repository.get_or_create_attempt(practice_set["id"], user_key)
        return {"practice_set": practice_set, "attempt": attempt}

    def save_answer(self, slug: str, user_key: str, question_number: int, answer: str) -> dict:
        workspace = self.get_practice_workspace(slug, user_key)
        questions = self._all_questions(workspace["practice_set"])
        if question_number not in {question["number"] for question in questions}:
            raise LookupError("Question not found in this practice set")
        attempt = self.repository.save_answer(workspace["attempt"]["id"], question_number, answer)
        return {
            "attempt_id": attempt["id"],
            "question_number": question_number,
            "answer": attempt["answers"].get(str(question_number), ""),
            "answered_count": sum(bool(value.strip()) for value in attempt["answers"].values()),
            "total": len(questions),
        }

    def submit(self, slug: str, user_key: str) -> dict:
        workspace = self.get_practice_workspace(slug, user_key)
        questions = self._all_questions(workspace["practice_set"])
        answers = {
            int(number): value for number, value in workspace["attempt"]["answers"].items()
        }
        missing = tuple(
            question["number"]
            for question in questions
            if not answers.get(question["number"], "").strip()
        )
        if missing:
            raise IncompleteAttemptError(missing)

        grade = grade_answers([self._to_entity(question) for question in questions], answers)
        attempt = self.repository.submit_attempt(workspace["attempt"]["id"], grade)
        return {
            "attempt_id": attempt["id"],
            "score": grade.score,
            "total": grade.total,
            "status": attempt["status"],
            "questions": attempt["results"],
        }

    def get_audio_path(self, slug: str, section_number: int) -> str:
        practice_set = self._require_set(slug)
        section = next(
            (item for item in practice_set["sections"] if item["order_index"] == section_number),
            None,
        )
        if section is None or not section["audio_path"]:
            raise LookupError("Audio not found")
        return section["audio_path"]

    def _require_set(self, slug: str) -> dict:
        practice_set = self.repository.get_practice_set(slug)
        if practice_set is None:
            raise PracticeSetNotFoundError(slug)
        return practice_set

    @staticmethod
    def _all_questions(practice_set: dict) -> list[dict]:
        return [question for section in practice_set["sections"] for question in section["questions"]]

    @staticmethod
    def _to_entity(question: dict) -> PracticeQuestion:
        return PracticeQuestion(
            number=question["number"],
            prompt=question["prompt"],
            question_type=QuestionType(question["question_type"]),
            accepted_answers=tuple(question["accepted_answers"]),
            explanation=question["explanation"],
            options=tuple(
                QuestionOption(key=option["key"], text=option["text"])
                for option in question["options"]
            ),
            answer_group=question["answer_group"],
        )

