from dataclasses import dataclass, field
from enum import StrEnum


class QuestionType(StrEnum):
    TEXT = "text"
    SINGLE_CHOICE = "single_choice"
    TRUE_FALSE_NOT_GIVEN = "true_false_not_given"


@dataclass(frozen=True)
class QuestionOption:
    key: str
    text: str


@dataclass(frozen=True)
class PracticeQuestion:
    number: int
    prompt: str
    question_type: QuestionType
    accepted_answers: tuple[str, ...]
    explanation: str
    options: tuple[QuestionOption, ...] = field(default_factory=tuple)
    answer_group: str | None = None


@dataclass(frozen=True)
class QuestionResult:
    number: int
    submitted_answer: str
    correct_answers: tuple[str, ...]
    is_correct: bool
    explanation: str


@dataclass(frozen=True)
class GradeResult:
    score: int
    total: int
    questions: tuple[QuestionResult, ...]

