from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request

from app.config import settings


@dataclass(frozen=True, slots=True)
class LearnerContext:
    """Authenticated learner identity at the HTTP boundary.

    The local adapter intentionally returns one configured learner. A future auth
    adapter can replace this FastAPI dependency without changing application
    services or allowing the browser to choose another learner key.
    """

    user_key: str


def get_learner_context(request: Request) -> LearnerContext:
    del request
    return LearnerContext(user_key=settings.local_user_key)


Learner = Annotated[LearnerContext, Depends(get_learner_context)]
