from collections.abc import Callable
from datetime import datetime, timezone

from app.domain.learning_evidence.entities import (
    CompletedStudySession,
    LearningEvidenceBundle,
    Skill,
    SkillPerformanceEvidence,
)
from app.domain.resources.repository import ResourceRepository
from app.domain.speaking.entities import (
    RetellingDraft,
    RetellingRecord,
    RetellingSubmission,
    RetellingWorkspaceInput,
    ShadowingSentence,
    ShadowingSentenceProgress,
    SpeakingPracticeStatus,
    SpeakingWorkspace,
)
from app.domain.speaking.repository import SpeakingPracticeRepository
from app.services.learning_evidence import LearningEvidenceService
from app.services.learner_profile import LearnerProfileService
from app.services.weakness_detection import WeaknessDetectionService


class InvalidRetellingError(ValueError):
    pass


class IncompleteRetellingError(InvalidRetellingError):
    pass


class SpeakingPracticeService:
    def __init__(
        self,
        repository: SpeakingPracticeRepository,
        resource_repository: ResourceRepository,
        evidence_service: LearningEvidenceService | None = None,
        learner_profile_service: LearnerProfileService | None = None,
        weakness_detection_service: WeaknessDetectionService | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.repository = repository
        self.resource_repository = resource_repository
        self.evidence_service = evidence_service
        self.learner_profile_service = learner_profile_service
        self.weakness_detection_service = weakness_detection_service
        self.now = now or utc_now

    def save_retelling(self, user_key: str, draft: RetellingDraft) -> RetellingRecord:
        normalized = _normalize_draft(draft)
        if normalized.source_resource_id is not None and self.resource_repository.get(
            normalized.source_resource_id
        ) is None:
            raise InvalidRetellingError("Source resource not found")
        return self.repository.create(user_key, normalized)

    def list_retellings(
        self,
        user_key: str,
        search: str = "",
        limit: int = 200,
    ) -> tuple[RetellingRecord, ...]:
        if limit < 1 or limit > 500:
            raise ValueError("limit must be between 1 and 500")
        return self.repository.list_records(user_key, search.strip(), limit)

    def get_workspace(self, user_key: str, resource_id: int) -> SpeakingWorkspace:
        resource = self.resource_repository.get(resource_id)
        if resource is None:
            raise LookupError("Speaking resource not found")
        if resource.skill is not Skill.SPEAKING:
            raise InvalidRetellingError("This resource is not a speaking task")
        practice = resource.content.get("speaking_practice")
        if not isinstance(practice, dict):
            raise InvalidRetellingError("Speaking practice content is unavailable")

        audio = practice.get("audio")
        if not isinstance(audio, dict):
            raise InvalidRetellingError("Speaking practice audio is unavailable")
        audio_slug = str(audio.get("practice_set_slug", "")).strip()
        try:
            audio_section = int(audio.get("section_number", 0))
        except (TypeError, ValueError) as error:
            raise InvalidRetellingError("Speaking practice audio is invalid") from error
        if not audio_slug or not 1 <= audio_section <= 4:
            raise InvalidRetellingError("Speaking practice audio is invalid")

        progress = {
            item.sentence_key: item
            for item in self.repository.list_sentence_progress(user_key, resource_id)
        }
        sentences = _parse_sentences(practice.get("sentences"), progress)
        if not sentences:
            raise InvalidRetellingError("Speaking practice sentences are unavailable")
        prompt = str(practice.get("retelling_prompt", "")).strip()
        if not prompt:
            raise InvalidRetellingError("Speaking retelling prompt is unavailable")
        return SpeakingWorkspace(
            resource=resource,
            record=self.repository.get_workspace_record(user_key, resource_id),
            audio_url=f"/media/audio/{audio_slug}/{audio_section}",
            source_label=str(audio.get("label", "Real conversation audio")),
            context=str(practice.get("context", "")).strip(),
            workflow=tuple(
                str(value)
                for value in practice.get(
                    "workflow",
                    ["Listen", "Pause", "Repeat", "Imitate", "Hide transcript", "Retell"],
                )
            ),
            sentences=sentences,
            retelling_prompt=prompt,
            retelling_guidance=tuple(
                str(value) for value in practice.get("retelling_guidance", [])
            ),
        )

    def save_workspace_draft(
        self,
        user_key: str,
        resource_id: int,
        draft_input: RetellingWorkspaceInput,
    ) -> RetellingRecord:
        workspace = self.get_workspace(user_key, resource_id)
        validated = _validate_workspace_input(draft_input)
        return self.repository.save_workspace_record(
            user_key,
            resource_id,
            workspace.retelling_prompt,
            workspace.context,
            validated,
            self.now(),
        )

    def mark_sentence(
        self,
        user_key: str,
        resource_id: int,
        sentence_key: str,
        practice_status: SpeakingPracticeStatus,
    ) -> ShadowingSentenceProgress:
        workspace = self.get_workspace(user_key, resource_id)
        valid_keys = {sentence.key for sentence in workspace.sentences}
        if sentence_key not in valid_keys:
            raise LookupError("Shadowing sentence not found")
        return self.repository.save_sentence_progress(
            user_key,
            resource_id,
            sentence_key,
            practice_status,
            self.now(),
        )

    def submit(
        self,
        user_key: str,
        resource_id: int,
    ) -> tuple[RetellingRecord, RetellingSubmission, int]:
        workspace = self.get_workspace(user_key, resource_id)
        record = workspace.record
        if record is None:
            raise InvalidRetellingError("请先保存复述内容。")
        if not record.written_outline.strip() and not record.retelling_text.strip():
            raise IncompleteRetellingError("请至少保存复述提纲或复述文字后再提交。")
        record, submission = self.repository.submit_workspace_record(
            user_key,
            resource_id,
            self.now(),
        )
        study_session_id = self._record_submission(workspace, record, submission)
        return record, submission, study_session_id

    def _record_submission(
        self,
        workspace: SpeakingWorkspace,
        record: RetellingRecord,
        submission: RetellingSubmission,
    ) -> int:
        if (
            self.evidence_service is None
            or self.learner_profile_service is None
            or self.weakness_detection_service is None
        ):
            raise RuntimeError("Speaking evidence services are not configured")
        marked = tuple(
            sentence.progress
            for sentence in workspace.sentences
            if sentence.progress is not None
        )
        recorded = self.evidence_service.record(
            build_speaking_evidence_bundle(workspace, record, submission, marked)
        )
        self.learner_profile_service.refresh_profile(record.user_key)
        self.weakness_detection_service.refresh_assessment(record.user_key)
        return recorded.study_session_id


def build_speaking_evidence_bundle(
    workspace: SpeakingWorkspace,
    record: RetellingRecord,
    submission: RetellingSubmission,
    marked_sentences: tuple[ShadowingSentenceProgress, ...],
) -> LearningEvidenceBundle:
    needs_practice_count = sum(
        item.practice_status is SpeakingPracticeStatus.NEED_PRACTICE
        for item in marked_sentences
    )
    session = CompletedStudySession(
        user_key=record.user_key,
        resource_id=record.source_resource_id or workspace.resource.id,
        skill=Skill.SPEAKING,
        source_type="speaking_retelling",
        source_id=str(record.id),
        source_revision=submission.revision,
        started_at=record.started_at,
        completed_at=submission.submitted_at,
        accuracy=None,
        attempt_count=submission.revision,
        incorrect_item_count=0,
        actual_duration_seconds=submission.active_duration_seconds,
        perceived_difficulty=submission.perceived_difficulty,
        confidence=submission.confidence,
        hard_item_count=needs_practice_count,
        notes=submission.written_outline_snapshot,
    )
    performance = SkillPerformanceEvidence(
        user_key=record.user_key,
        skill=Skill.SPEAKING,
        accuracy=None,
        item_count=len(marked_sentences),
        correct_item_count=0,
        incorrect_item_count=0,
        hard_item_count=needs_practice_count,
        occurred_at=submission.submitted_at,
        confidence=submission.confidence,
        perceived_difficulty=submission.perceived_difficulty,
        metrics={
            "evidence_type": "speaking_retelling_submission",
            "submission_revision": submission.revision,
            "active_duration_seconds": submission.active_duration_seconds,
            "marked_sentence_count": len(marked_sentences),
            "needs_practice_count": needs_practice_count,
            "mastered_sentence_count": sum(
                item.practice_status is SpeakingPracticeStatus.MASTERED
                for item in marked_sentences
            ),
            "intended_chunk_count": len(submission.intended_vocabulary_snapshot),
            "has_retelling_text": bool(submission.retelling_text_snapshot.strip()),
            "awaiting_ai_evaluation": True,
        },
    )
    return LearningEvidenceBundle(session=session, exercises=(), performance=performance)


def _parse_sentences(
    payload: object,
    progress: dict[str, ShadowingSentenceProgress],
) -> tuple[ShadowingSentence, ...]:
    if not isinstance(payload, list):
        return ()
    parsed: list[ShadowingSentence] = []
    seen: set[str] = set()
    for item in payload:
        if not isinstance(item, dict):
            raise InvalidRetellingError("Speaking sentence content is invalid")
        key = str(item.get("key", "")).strip()
        text = str(item.get("text", "")).strip()
        if not key or not text or key in seen:
            raise InvalidRetellingError("Speaking sentence content is invalid")
        seen.add(key)
        chunks = item.get("chunks", [])
        if not isinstance(chunks, list):
            raise InvalidRetellingError("Speaking sentence chunks are invalid")
        parsed.append(
            ShadowingSentence(
                key=key,
                speaker=str(item.get("speaker", "Speaker")).strip() or "Speaker",
                text=text,
                pronunciation_note=str(item.get("pronunciation_note", "")).strip(),
                connected_speech_note=str(item.get("connected_speech_note", "")).strip(),
                chunks=tuple(str(value).strip() for value in chunks if str(value).strip()),
                progress=progress.get(key),
            )
        )
    return tuple(parsed)


def _normalize_draft(draft: RetellingDraft) -> RetellingDraft:
    prompt = " ".join(draft.prompt.split())
    if not prompt:
        raise InvalidRetellingError("Retelling prompt is required")
    vocabulary = _normalize_vocabulary(draft.intended_vocabulary)
    return RetellingDraft(
        prompt=prompt,
        written_outline=draft.written_outline.strip(),
        intended_vocabulary=vocabulary,
        retelling_text=draft.retelling_text.strip(),
        mistakes=draft.mistakes.strip(),
        improved_version=draft.improved_version.strip(),
        practice_status=draft.practice_status,
        source_resource_id=draft.source_resource_id,
        source_context=draft.source_context.strip(),
        voice_recording_reference=draft.voice_recording_reference,
        workspace_managed=draft.workspace_managed,
        active_duration_seconds=draft.active_duration_seconds,
        perceived_difficulty=draft.perceived_difficulty,
        confidence=draft.confidence,
    )


def _validate_workspace_input(
    draft_input: RetellingWorkspaceInput,
) -> RetellingWorkspaceInput:
    limits = (
        ("Outline", draft_input.written_outline, 12_000),
        ("Retelling", draft_input.retelling_text, 20_000),
        ("Mistakes", draft_input.mistakes, 12_000),
        ("Improved version", draft_input.improved_version, 20_000),
    )
    for label, value, maximum in limits:
        if len(value) > maximum:
            raise InvalidRetellingError(f"{label} must be {maximum:,} characters or fewer")
    if not 0 <= draft_input.active_duration_seconds <= 28_800:
        raise InvalidRetellingError("Active duration must be between 0 and 8 hours")
    for label, value in (
        ("Difficulty", draft_input.perceived_difficulty),
        ("Confidence", draft_input.confidence),
    ):
        if value is not None and not 1 <= value <= 5:
            raise InvalidRetellingError(f"{label} must be between 1 and 5")
    vocabulary = _normalize_vocabulary(draft_input.intended_vocabulary)
    if len(vocabulary) > 40:
        raise InvalidRetellingError("Use 40 intended chunks or fewer")
    return RetellingWorkspaceInput(
        written_outline=draft_input.written_outline.strip(),
        intended_vocabulary=vocabulary,
        retelling_text=draft_input.retelling_text.strip(),
        mistakes=draft_input.mistakes.strip(),
        improved_version=draft_input.improved_version.strip(),
        practice_status=draft_input.practice_status,
        active_duration_seconds=draft_input.active_duration_seconds,
        perceived_difficulty=draft_input.perceived_difficulty,
        confidence=draft_input.confidence,
    )


def _normalize_vocabulary(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        value
        for value in dict.fromkeys(" ".join(item.split()) for item in values)
        if value
    )


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
