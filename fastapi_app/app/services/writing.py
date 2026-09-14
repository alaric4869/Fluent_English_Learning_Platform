import re
from collections.abc import Callable
from datetime import datetime, timezone

from app.domain.learning_evidence.entities import (
    CompletedStudySession,
    LearningEvidenceBundle,
    Skill,
    SkillPerformanceEvidence,
)
from app.domain.resources.repository import ResourceRepository
from app.domain.writing.entities import (
    WritingDraft,
    WritingDraftInput,
    WritingSubmission,
    WritingWorkspace,
)
from app.domain.writing.repository import WritingRepository
from app.services.learning_evidence import LearningEvidenceService
from app.services.learner_profile import LearnerProfileService
from app.services.weakness_detection import WeaknessDetectionService


class InvalidWritingDraftError(ValueError):
    pass


class IncompleteWritingDraftError(InvalidWritingDraftError):
    def __init__(self, word_count: int, minimum_words: int) -> None:
        self.word_count = word_count
        self.minimum_words = minimum_words
        super().__init__(
            f"当前 {word_count} 词；达到 {minimum_words} 词后才能提交。"
        )


class WritingPracticeService:
    def __init__(
        self,
        repository: WritingRepository,
        resource_repository: ResourceRepository,
        evidence_service: LearningEvidenceService,
        learner_profile_service: LearnerProfileService,
        weakness_detection_service: WeaknessDetectionService,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.repository = repository
        self.resource_repository = resource_repository
        self.evidence_service = evidence_service
        self.learner_profile_service = learner_profile_service
        self.weakness_detection_service = weakness_detection_service
        self.now = now or utc_now

    def get_workspace(self, user_key: str, resource_id: int) -> WritingWorkspace:
        resource = self.resource_repository.get(resource_id)
        if resource is None:
            raise LookupError("Writing resource not found")
        if resource.skill is not Skill.WRITING:
            raise InvalidWritingDraftError("This resource is not a writing task")
        task = resource.content.get("writing_task")
        if not isinstance(task, dict):
            raise InvalidWritingDraftError("Writing task content is unavailable")
        try:
            minimum_words = int(task["minimum_words"])
            recommended_minutes = int(task["recommended_minutes"])
        except (KeyError, TypeError, ValueError) as error:
            raise InvalidWritingDraftError("Writing task settings are invalid") from error
        if minimum_words < 1 or recommended_minutes < 1:
            raise InvalidWritingDraftError("Writing task settings are invalid")
        return WritingWorkspace(
            resource=resource,
            draft=self.repository.get_draft(user_key, resource_id),
            minimum_words=minimum_words,
            recommended_minutes=recommended_minutes,
            task_type=str(task.get("task_type", "Writing task")),
            instructions=str(task.get("instructions", "")),
            situation=str(task.get("situation", "")),
            prompt=str(task.get("prompt", "")),
            bullet_points=tuple(str(value) for value in task.get("bullet_points", [])),
            closing_instruction=str(task.get("closing_instruction", "")),
        )

    def save_draft(
        self,
        user_key: str,
        resource_id: int,
        draft_input: WritingDraftInput,
    ) -> WritingDraft:
        self.get_workspace(user_key, resource_id)
        validated = _validate_input(draft_input)
        return self.repository.save_draft(
            user_key,
            resource_id,
            validated,
            count_words(validated.response_text),
            self.now(),
        )

    def submit(
        self,
        user_key: str,
        resource_id: int,
    ) -> tuple[WritingDraft, WritingSubmission, int]:
        workspace = self.get_workspace(user_key, resource_id)
        draft = workspace.draft
        if draft is None:
            raise InvalidWritingDraftError("请先保存写作内容。")
        if draft.word_count < workspace.minimum_words:
            raise IncompleteWritingDraftError(
                draft.word_count,
                workspace.minimum_words,
            )
        occurred_at = self.now()
        draft, submission = self.repository.submit(
            user_key,
            resource_id,
            occurred_at,
        )
        recorded = self.evidence_service.record(
            build_writing_evidence_bundle(
                workspace,
                draft,
                submission,
            )
        )
        self.learner_profile_service.refresh_profile(user_key)
        self.weakness_detection_service.refresh_assessment(user_key)
        return draft, submission, recorded.study_session_id


def build_writing_evidence_bundle(
    workspace: WritingWorkspace,
    draft: WritingDraft,
    submission: WritingSubmission,
) -> LearningEvidenceBundle:
    session = CompletedStudySession(
        user_key=draft.user_key,
        resource_id=draft.resource_id,
        skill=Skill.WRITING,
        source_type="writing_draft",
        source_id=str(draft.id),
        source_revision=submission.revision,
        started_at=draft.started_at,
        completed_at=submission.submitted_at,
        accuracy=None,
        attempt_count=submission.revision,
        incorrect_item_count=0,
        actual_duration_seconds=submission.active_duration_seconds,
        perceived_difficulty=submission.perceived_difficulty,
        confidence=submission.confidence,
        notes=submission.outline_snapshot,
    )
    performance = SkillPerformanceEvidence(
        user_key=draft.user_key,
        skill=Skill.WRITING,
        accuracy=None,
        item_count=0,
        correct_item_count=0,
        incorrect_item_count=0,
        occurred_at=submission.submitted_at,
        confidence=submission.confidence,
        perceived_difficulty=submission.perceived_difficulty,
        metrics={
            "evidence_type": "writing_submission",
            "word_count": submission.word_count,
            "minimum_words": workspace.minimum_words,
            "task_type": workspace.task_type,
            "submission_revision": submission.revision,
            "active_duration_seconds": submission.active_duration_seconds,
            "awaiting_ai_evaluation": True,
        },
    )
    return LearningEvidenceBundle(session=session, exercises=(), performance=performance)


def count_words(value: str) -> int:
    return len(re.findall(r"\b[\w]+(?:['’-][\w]+)*\b", value, flags=re.UNICODE))


def _validate_input(draft_input: WritingDraftInput) -> WritingDraftInput:
    if len(draft_input.response_text) > 30_000:
        raise InvalidWritingDraftError("Writing response must be 30,000 characters or fewer")
    if len(draft_input.outline) > 12_000:
        raise InvalidWritingDraftError("Outline must be 12,000 characters or fewer")
    if not 0 <= draft_input.active_duration_seconds <= 28_800:
        raise InvalidWritingDraftError("Active duration must be between 0 and 8 hours")
    for label, value in (
        ("Difficulty", draft_input.perceived_difficulty),
        ("Confidence", draft_input.confidence),
    ):
        if value is not None and not 1 <= value <= 5:
            raise InvalidWritingDraftError(f"{label} must be between 1 and 5")
    return draft_input


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
