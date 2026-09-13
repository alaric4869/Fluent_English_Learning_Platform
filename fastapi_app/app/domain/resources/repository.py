from datetime import date
from typing import Protocol

from app.domain.learning_evidence.entities import Skill
from app.domain.resources.entities import ResourceCandidate


class ResourceRepository(Protocol):
    def list_candidates(
        self,
        user_key: str,
        skill: Skill,
        target_date: date,
    ) -> tuple[ResourceCandidate, ...]: ...
