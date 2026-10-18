import hashlib
import json
from collections.abc import Callable
from datetime import datetime, timezone

from app.domain.learning_evidence.entities import Skill
from app.domain.weakness_detection.detector import WeaknessDetector
from app.domain.weakness_detection.entities import (
    SkillWeaknessAssessment,
    WeaknessAssessmentEvaluation,
    WeaknessAssessmentRun,
)
from app.domain.weakness_detection.repository import WeaknessAssessmentRepository
from app.services.learner_profile import LearnerProfileService


class WeaknessDetectionService:
    def __init__(
        self,
        profile_service: LearnerProfileService,
        repository: WeaknessAssessmentRepository,
        detector: WeaknessDetector,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.profile_service = profile_service
        self.repository = repository
        self.detector = detector
        self.now = now or utc_now

    def refresh_assessment(self, user_key: str) -> WeaknessAssessmentRun:
        if self.profile_service.get_current_profile(user_key) is None:
            self.profile_service.refresh_profile(user_key)
        skill_assessments = tuple(self._detect_skill(user_key, skill) for skill in Skill)
        evaluation = WeaknessAssessmentEvaluation(
            user_key=user_key,
            assessed_at=self.now(),
            detector_version=self.detector.detector_version,
            evidence_fingerprint=_evidence_fingerprint(
                self.detector.detector_version,
                skill_assessments,
            ),
            skills=skill_assessments,
        )
        return self.repository.save_run(evaluation)

    def get_current_assessment(self, user_key: str) -> WeaknessAssessmentRun | None:
        return self.repository.get_latest(user_key)

    def _detect_skill(self, user_key: str, skill: Skill) -> SkillWeaknessAssessment:
        history = self.profile_service.get_recent_skill_profiles(
            user_key,
            skill,
            self.detector.recent_snapshot_limit,
        )
        return self.detector.detect(skill, history)


def _evidence_fingerprint(
    detector_version: str,
    skills: tuple[SkillWeaknessAssessment, ...],
) -> str:
    payload = {
        "detector_version": detector_version,
        "evidence": {
            item.skill.value: list(item.evidence_snapshot_ids)
            for item in sorted(skills, key=lambda value: value.skill.value)
        },
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
