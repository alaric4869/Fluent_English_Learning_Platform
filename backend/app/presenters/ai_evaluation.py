from app.domain.ai_evaluation.entities import StoredWorkEvaluation


def present_work_evaluation(evaluation: StoredWorkEvaluation) -> dict:
    return {
        "id": evaluation.id,
        "source_revision": evaluation.request.source_revision,
        "provider_name": evaluation.result.provider_name,
        "model_name": evaluation.result.model_name,
        "overall_score": evaluation.result.overall_score,
        "summary": evaluation.result.summary,
        "criteria": [
            {
                "key": item.key,
                "label": item.label,
                "score": item.score,
                "maximum_score": item.maximum_score,
                "explanation": item.explanation,
                "evidence": list(item.evidence),
            }
            for item in evaluation.result.criteria
        ],
        "strengths": list(evaluation.result.strengths),
        "improvement_priorities": list(evaluation.result.improvement_priorities),
        "corrections": [
            {
                "original": item.original,
                "suggested": item.suggested,
                "reason": item.reason,
            }
            for item in evaluation.result.corrections
        ],
        "suggested_revision": evaluation.result.suggested_revision,
        "created_at": evaluation.created_at,
        "created": evaluation.created,
    }
