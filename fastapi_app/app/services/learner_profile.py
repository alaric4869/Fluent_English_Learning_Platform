import hashlib
import json
from collections.abc import Callable
from datetime import datetime, timezone

from app.domain.learning_evidence.entities import Skill
from app.domain.learner_profile.entities import (
    HistoricalSkillProfile,
    LearnerProfileEvaluation,
    LearnerProfileSnapshot,
    SkillProfileEvaluation,
)
from app.domain.learner_profile.evaluator import SkillEvaluator
from app.domain.learner_profile.repository import LearnerProfileRepository
from app.services.learning_evidence import LearningEvidenceService


class LearnerProfileService:
    def __init__(
        self,
        evidence_service: LearningEvidenceService,
        repository: LearnerProfileRepository,
        evaluator: SkillEvaluator,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.evidence_service = evidence_service
        self.repository = repository
        self.evaluator = evaluator
        self.now = now or utc_now

    def refresh_profile(self, user_key: str) -> LearnerProfileSnapshot:
        skill_evaluations = tuple(self._evaluate_skill(user_key, skill) for skill in Skill)
        evaluation = LearnerProfileEvaluation(
            user_key=user_key,
            calculated_at=self.now(),
            algorithm_version=self.evaluator.algorithm_version,
            evidence_fingerprint=_evidence_fingerprint(
                self.evaluator.algorithm_version,
                skill_evaluations,
            ),
            skills=skill_evaluations,
        )
        return self.repository.save_snapshot(evaluation)

    def get_current_profile(self, user_key: str) -> LearnerProfileSnapshot | None:
        return self.repository.get_latest(user_key)

    def get_recent_skill_profiles(
        self,
        user_key: str,
        skill: Skill,
        limit: int,
    ) -> tuple[HistoricalSkillProfile, ...]:
        if limit < 1:
            raise ValueError("limit must be positive")
        return self.repository.list_recent_skill_profiles(user_key, skill, limit)

    def _evaluate_skill(self, user_key: str, skill: Skill) -> SkillProfileEvaluation:
        history = self.evidence_service.get_recent_skill_performance(
            user_key,
            skill,
            self.evaluator.recent_session_limit,
        )
        return self.evaluator.evaluate(skill, history)


def _evidence_fingerprint(
    algorithm_version: str,
    skills: tuple[SkillProfileEvaluation, ...],
) -> str:
    payload = {
        "algorithm_version": algorithm_version,
        "evidence": {
            item.skill.value: list(item.evidence_ids)
            for item in sorted(skills, key=lambda value: value.skill.value)
        },
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
