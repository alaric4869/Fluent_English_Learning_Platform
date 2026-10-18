from pydantic import BaseModel, Field


class SaveAnswerRequest(BaseModel):
    answer: str = Field(max_length=500)


class SavedAnswerResponse(BaseModel):
    attempt_id: int
    question_number: int
    answer: str
    answered_count: int
    total: int


class QuestionResultResponse(BaseModel):
    number: int
    submitted_answer: str
    correct_answers: list[str]
    is_correct: bool
    explanation: str


class SubmitAttemptResponse(BaseModel):
    attempt_id: int
    score: int
    total: int
    status: str
    questions: list[QuestionResultResponse]

