import hashlib
import json

from app.domain.ai_evaluation.entities import (
    EvaluationSourceType,
    StoredWorkEvaluation,
    WorkEvaluationRequest,
)
from app.domain.ai_evaluation.evaluator import WorkEvaluator
from app.domain.ai_evaluation.repository import WorkEvaluationRepository
from app.domain.learning_evidence.entities import Skill
from app.domain.resources.repository import ResourceRepository
from app.domain.speaking.repository import SpeakingPracticeRepository
from app.domain.writing.repository import WritingRepository


class LearningWorkEvaluationService:
    def __init__(
        self,
        repository: WorkEvaluationRepository,
        evaluator: WorkEvaluator,
        resource_repository: ResourceRepository,
        writing_repository: WritingRepository,
        speaking_repository: SpeakingPracticeRepository,
    ) -> None:
        self.repository = repository
        self.evaluator = evaluator
        self.resource_repository = resource_repository
        self.writing_repository = writing_repository
        self.speaking_repository = speaking_repository

    @property
    def available(self) -> bool:
        return self.evaluator.available

    def evaluate_writing(
        self,
        user_key: str,
        resource_id: int,
        revision: int | None = None,
    ) -> StoredWorkEvaluation:
        resource = self.resource_repository.get(resource_id)
        if resource is None or resource.skill is not Skill.WRITING:
            raise LookupError("Writing resource not found")
        submission = self.writing_repository.get_submission(
            user_key,
            resource_id,
            revision,
        )
        if submission is None:
            raise LookupError("Submitted writing revision not found")
        task = resource.content.get("writing_task")
        if not isinstance(task, dict):
            raise InvalidEvaluationSourceError("Writing task content is unavailable")
        request = _request(
            user_key=user_key,
            resource_id=resource_id,
            skill=Skill.WRITING,
            source_type=EvaluationSourceType.WRITING_SUBMISSION,
            source_id=submission.id,
            source_revision=submission.revision,
            task_prompt=_writing_prompt(task),
            learner_text=submission.response_snapshot,
            supporting_context=submission.outline_snapshot,
        )
        return self._evaluate(request)

    def evaluate_retelling(
        self,
        user_key: str,
        resource_id: int,
        revision: int | None = None,
    ) -> StoredWorkEvaluation:
        resource = self.resource_repository.get(resource_id)
        if resource is None or resource.skill is not Skill.SPEAKING:
            raise LookupError("Speaking resource not found")
        record = self.speaking_repository.get_workspace_record(user_key, resource_id)
        submission = self.speaking_repository.get_workspace_submission(
            user_key,
            resource_id,
            revision,
        )
        if record is None or submission is None:
            raise LookupError("Submitted retelling revision not found")
        learner_text = (
            submission.retelling_text_snapshot.strip()
            or submission.improved_version_snapshot.strip()
        )
        if not learner_text:
            raise InvalidEvaluationSourceError(
                "A written retelling is required for text evaluation"
            )
        supporting_context = json.dumps(
            {
                "outline": submission.written_outline_snapshot,
                "intended_chunks": list(submission.intended_vocabulary_snapshot),
                "learner_identified_mistakes": submission.mistakes_snapshot,
            },
            ensure_ascii=False,
        )
        request = _request(
            user_key=user_key,
            resource_id=resource_id,
            skill=Skill.SPEAKING,
            source_type=EvaluationSourceType.RETELLING_SUBMISSION,
            source_id=submission.id,
            source_revision=submission.revision,
            task_prompt=record.prompt,
            learner_text=learner_text,
            supporting_context=supporting_context,
        )
        return self._evaluate(request)

    def get_latest_writing_evaluation(
        self,
        user_key: str,
        resource_id: int,
    ) -> StoredWorkEvaluation | None:
        submission = self.writing_repository.get_submission(user_key, resource_id)
        if submission is None:
            return None
        return self.repository.get_latest_for_source(
            user_key,
            EvaluationSourceType.WRITING_SUBMISSION.value,
            submission.id,
        )

    def get_latest_retelling_evaluation(
        self,
        user_key: str,
        resource_id: int,
    ) -> StoredWorkEvaluation | None:
        submission = self.speaking_repository.get_workspace_submission(
            user_key,
            resource_id,
        )
        if submission is None:
            return None
        return self.repository.get_latest_for_source(
            user_key,
            EvaluationSourceType.RETELLING_SUBMISSION.value,
            submission.id,
        )

    def _evaluate(self, request: WorkEvaluationRequest) -> StoredWorkEvaluation:
        existing = self.repository.get_existing(
            request,
            self.evaluator.evaluator_version,
        )
        if existing is not None:
            return existing
        result = self.evaluator.evaluate(request)
        if not 0 <= result.overall_score <= 100:
            raise InvalidEvaluationResultError(
                "Evaluation score must be between 0 and 100"
            )
        if result.evaluator_version != self.evaluator.evaluator_version:
            raise InvalidEvaluationResultError("Evaluator version mismatch")
        return self.repository.save(request, result)


def _request(
    *,
    user_key: str,
    resource_id: int,
    skill: Skill,
    source_type: EvaluationSourceType,
    source_id: int,
    source_revision: int,
    task_prompt: str,
    learner_text: str,
    supporting_context: str,
) -> WorkEvaluationRequest:
    fingerprint_payload = {
        "source_type": source_type.value,
        "source_id": source_id,
        "source_revision": source_revision,
        "task_prompt": task_prompt,
        "learner_text": learner_text,
        "supporting_context": supporting_context,
    }
    fingerprint = hashlib.sha256(
        json.dumps(
            fingerprint_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return WorkEvaluationRequest(
        user_key=user_key,
        resource_id=resource_id,
        skill=skill,
        source_type=source_type,
        source_id=source_id,
        source_revision=source_revision,
        task_prompt=task_prompt,
        learner_text=learner_text,
        supporting_context=supporting_context,
        input_fingerprint=fingerprint,
    )


def _writing_prompt(task: dict) -> str:
    parts = [
        str(task.get("instructions", "")).strip(),
        str(task.get("situation", "")).strip(),
        str(task.get("prompt", "")).strip(),
    ]
    bullet_points = task.get("bullet_points", [])
    if isinstance(bullet_points, list):
        parts.extend(f"- {item}" for item in bullet_points)
    parts.append(str(task.get("closing_instruction", "")).strip())
    return "\n".join(item for item in parts if item)


class InvalidEvaluationSourceError(ValueError):
    pass


class InvalidEvaluationResultError(ValueError):
    pass
