import json
from pathlib import Path

import pytest

from app.services.ielts_practice import IeltsPracticeService, IncompleteAttemptError


class FakeRepository:
    def __init__(self) -> None:
        self.practice_set = {
            "id": 1,
            "slug": "test-set",
            "sections": [
                {
                    "order_index": 1,
                    "audio_path": None,
                    "questions": [
                        {
                            "number": 1,
                            "prompt": "Question",
                            "question_type": "text",
                            "accepted_answers": ["answer"],
                            "explanation": "Explanation",
                            "options": [],
                            "answer_group": None,
                        }
                    ],
                }
            ],
        }
        self.attempt = {"id": 2, "answers": {}, "results": [], "status": "in_progress", "score": None}

    def list_practice_sets(self) -> list[dict]:
        return [self.practice_set]

    def get_practice_set(self, slug: str) -> dict | None:
        return self.practice_set if slug == "test-set" else None

    def get_or_create_attempt(self, practice_set_id: int, user_key: str) -> dict:
        return self.attempt

    def get_attempt(self, attempt_id: int) -> dict | None:
        return self.attempt

    def save_answer(self, attempt_id: int, question_number: int, answer: str) -> dict:
        self.attempt["answers"][str(question_number)] = answer
        return self.attempt

    def submit_attempt(self, attempt_id: int, grade) -> dict:
        self.attempt["status"] = "submitted"
        self.attempt["score"] = grade.score
        self.attempt["results"] = [
            {
                "number": item.number,
                "submitted_answer": item.submitted_answer,
                "correct_answers": list(item.correct_answers),
                "is_correct": item.is_correct,
                "explanation": item.explanation,
            }
            for item in grade.questions
        ]
        return self.attempt


def test_submit_requires_every_answer() -> None:
    service = IeltsPracticeService(FakeRepository())

    with pytest.raises(IncompleteAttemptError) as error:
        service.submit("test-set", "user")

    assert error.value.missing_questions == (1,)


def test_saved_answer_can_be_submitted_and_graded() -> None:
    repository = FakeRepository()
    service = IeltsPracticeService(repository)

    service.save_answer("test-set", "user", 1, "Answer")
    result = service.submit("test-set", "user")

    assert result["score"] == 1
    assert result["questions"][0]["explanation"] == "Explanation"


def test_g20_seed_contains_two_complete_40_question_sets() -> None:
    seed_path = Path(__file__).parents[1] / "seed" / "g20_test1.json"
    payload = json.loads(seed_path.read_text(encoding="utf-8"))

    assert {item["skill"] for item in payload["practice_sets"]} == {"listening", "reading"}
    for practice_set in payload["practice_sets"]:
        questions = [question for section in practice_set["sections"] for question in section["questions"]]
        assert [question["number"] for question in questions] == list(range(1, 41))
        assert all(question["explanation"] for question in questions)

