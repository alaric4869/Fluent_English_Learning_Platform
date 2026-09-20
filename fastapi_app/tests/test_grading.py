from app.domain.ielts.entities import PracticeQuestion, QuestionType
from app.domain.ielts.grading import grade_answers, normalize_answer


def question(number: int, answer: str, group: str | None = None) -> PracticeQuestion:
    return PracticeQuestion(
        number=number,
        prompt=f"Question {number}",
        question_type=QuestionType.TEXT,
        accepted_answers=(answer,),
        explanation="Because",
        answer_group=group,
    )


def test_normalize_answer_ignores_case_whitespace_and_light_punctuation() -> None:
    assert normalize_answer("  Not   Given. ") == "not given"


def test_normalize_answer_accepts_common_ielts_number_formatting() -> None:
    assert normalize_answer("£125") == normalize_answer("125")
    assert normalize_answer("seventy-five") == normalize_answer("seventy five")


def test_grade_answers_accepts_alternative_spellings() -> None:
    item = PracticeQuestion(
        number=1,
        prompt="Spelling",
        question_type=QuestionType.TEXT,
        accepted_answers=("behaviour", "behavior"),
        explanation="Either spelling is valid.",
    )

    result = grade_answers([item], {1: "Behavior"})

    assert result.score == 1
    assert result.questions[0].is_correct is True


def test_grouped_answers_are_graded_without_order() -> None:
    questions = [question(17, "A", "pair"), question(18, "E", "pair")]

    result = grade_answers(questions, {17: "E", 18: "A"})

    assert result.score == 2
    assert all(item.is_correct for item in result.questions)


def test_grouped_answers_reject_duplicates() -> None:
    questions = [question(17, "A", "pair"), question(18, "E", "pair")]

    result = grade_answers(questions, {17: "A", 18: "A"})

    assert result.score == 0
