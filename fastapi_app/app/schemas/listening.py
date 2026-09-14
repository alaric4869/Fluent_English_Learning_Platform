from pydantic import BaseModel, Field

from app.domain.listening.entities import ListeningSentenceStatus


class TranscriptSentenceMarkRequest(BaseModel):
    sentence: str = Field(min_length=1, max_length=4000)
    practice_status: ListeningSentenceStatus
