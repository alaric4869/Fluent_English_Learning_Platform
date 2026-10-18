import re
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence

from app.domain.ielts.entities import GradeResult, PracticeQuestion, QuestionResult


_WHITESPACE = re.compile(r"\s+")
_WORD_SEPARATORS = re.compile(r"[-–—]")
_IGNORED_PUNCTUATION = re.compile(r"[.,;:!?‘’'\"$£()]")


def normalize_answer(value: str) -> str:
    normalized = value.strip().casefold()
    normalized = _WORD_SEPARATORS.sub(" ", normalized)
    normalized = _IGNORED_PUNCTUATION.sub("", normalized)
    return _WHITESPACE.sub(" ", normalized)


def grade_answers(
    questions: Sequence[PracticeQuestion], answers: Mapping[int, str]
) -> GradeResult:
    grouped: dict[str, list[PracticeQuestion]] = defaultdict(list)
    for question in questions:
        if question.answer_group:
            grouped[question.answer_group].append(question)

    group_outcomes: dict[str, bool] = {}
    for group_id, members in grouped.items():
        submitted = Counter(normalize_answer(answers.get(item.number, "")) for item in members)
        expected = Counter(normalize_answer(item.accepted_answers[0]) for item in members)
        group_outcomes[group_id] = submitted == expected

    results: list[QuestionResult] = []
    for question in questions:
        submitted = answers.get(question.number, "")
        if question.answer_group:
            is_correct = group_outcomes[question.answer_group]
        else:
            normalized = normalize_answer(submitted)
            is_correct = normalized in {
                normalize_answer(answer) for answer in question.accepted_answers
            }
        results.append(
            QuestionResult(
                number=question.number,
                submitted_answer=submitted,
                correct_answers=question.accepted_answers,
                is_correct=is_correct,
                explanation=question.explanation,
            )
        )

    return GradeResult(
        score=sum(result.is_correct for result in results),
        total=len(results),
        questions=tuple(results),
    )
