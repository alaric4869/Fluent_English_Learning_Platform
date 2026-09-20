from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.ai_evaluation.entities import (
    EvaluationCorrection,
    EvaluationCriterion,
    EvaluationSourceType,
    GeneratedWorkEvaluation,
    StoredWorkEvaluation,
    WorkEvaluationRequest,
)
from app.domain.learning_evidence.entities import Skill
from app.models.ai_evaluation import WorkEvaluationModel


class SqlAlchemyWorkEvaluationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_existing(
        self,
        request: WorkEvaluationRequest,
        evaluator_version: str,
    ) -> StoredWorkEvaluation | None:
        row = self.session.scalar(
            select(WorkEvaluationModel).where(
                WorkEvaluationModel.user_key == request.user_key,
                WorkEvaluationModel.source_type == request.source_type.value,
                WorkEvaluationModel.source_id == request.source_id,
                WorkEvaluationModel.source_revision == request.source_revision,
                WorkEvaluationModel.evaluator_version == evaluator_version,
                WorkEvaluationModel.input_fingerprint == request.input_fingerprint,
            )
        )
        return _to_evaluation(row, created=False) if row else None

    def get_latest_for_source(
        self,
        user_key: str,
        source_type: str,
        source_id: int,
    ) -> StoredWorkEvaluation | None:
        row = self.session.scalar(
            select(WorkEvaluationModel)
            .where(
                WorkEvaluationModel.user_key == user_key,
                WorkEvaluationModel.source_type == source_type,
                WorkEvaluationModel.source_id == source_id,
            )
            .order_by(WorkEvaluationModel.id.desc())
        )
        return _to_evaluation(row, created=False) if row else None

    def save(
        self,
        request: WorkEvaluationRequest,
        result: GeneratedWorkEvaluation,
    ) -> StoredWorkEvaluation:
        existing = self.get_existing(request, result.evaluator_version)
        if existing is not None:
            return existing
        row = WorkEvaluationModel(
            user_key=request.user_key,
            resource_id=request.resource_id,
            skill=request.skill.value,
            source_type=request.source_type.value,
            source_id=request.source_id,
            source_revision=request.source_revision,
            input_fingerprint=request.input_fingerprint,
            task_prompt=request.task_prompt,
            learner_text=request.learner_text,
            supporting_context=request.supporting_context,
            provider_name=result.provider_name,
            model_name=result.model_name,
            evaluator_version=result.evaluator_version,
            overall_score=result.overall_score,
            summary=result.summary,
            criteria=[
                {
                    "key": item.key,
                    "label": item.label,
                    "score": item.score,
                    "maximum_score": item.maximum_score,
                    "explanation": item.explanation,
                    "evidence": list(item.evidence),
                }
                for item in result.criteria
            ],
            strengths=list(result.strengths),
            improvement_priorities=list(result.improvement_priorities),
            corrections=[
                {
                    "original": item.original,
                    "suggested": item.suggested,
                    "reason": item.reason,
                }
                for item in result.corrections
            ],
            suggested_revision=result.suggested_revision,
        )
        self.session.add(row)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            existing = self.get_existing(request, result.evaluator_version)
            if existing is None:
                raise
            return existing
        self.session.refresh(row)
        return _to_evaluation(row, created=True)


def _to_evaluation(
    row: WorkEvaluationModel,
    *,
    created: bool,
) -> StoredWorkEvaluation:
    request = WorkEvaluationRequest(
        user_key=row.user_key,
        resource_id=row.resource_id,
        skill=Skill(row.skill),
        source_type=EvaluationSourceType(row.source_type),
        source_id=row.source_id,
        source_revision=row.source_revision,
        task_prompt=row.task_prompt,
        learner_text=row.learner_text,
        supporting_context=row.supporting_context,
        input_fingerprint=row.input_fingerprint,
    )
    result = GeneratedWorkEvaluation(
        provider_name=row.provider_name,
        model_name=row.model_name,
        evaluator_version=row.evaluator_version,
        overall_score=row.overall_score,
        summary=row.summary,
        criteria=tuple(EvaluationCriterion(**item) for item in row.criteria),
        strengths=tuple(row.strengths),
        improvement_priorities=tuple(row.improvement_priorities),
        corrections=tuple(EvaluationCorrection(**item) for item in row.corrections),
        suggested_revision=row.suggested_revision,
    )
    return StoredWorkEvaluation(
        id=row.id,
        request=request,
        result=result,
        created_at=_as_utc(row.created_at),
        created=created,
    )


def _as_utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
