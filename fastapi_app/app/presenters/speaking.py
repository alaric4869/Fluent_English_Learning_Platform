from app.domain.ai_evaluation.entities import StoredWorkEvaluation
from app.domain.speaking.entities import (
    RetellingRecord,
    ShadowingSentenceProgress,
    SpeakingWorkspace,
)
from app.presenters.ai_evaluation import present_work_evaluation


def present_speaking_workspace(
    workspace: SpeakingWorkspace,
    *,
    evaluation: StoredWorkEvaluation | None = None,
    evaluation_available: bool = False,
) -> dict:
    record = _present_record(workspace.record)
    marked_count = sum(sentence.progress is not None for sentence in workspace.sentences)
    mastered_count = sum(
        sentence.progress is not None
        and sentence.progress.practice_status.value == "mastered"
        for sentence in workspace.sentences
    )
    return {
        "active_page": "ielts",
        "workspace": workspace,
        "record": record,
        "marked_count": marked_count,
        "mastered_count": mastered_count,
        "evaluation": (
            present_work_evaluation(evaluation) if evaluation is not None else None
        ),
        "evaluation_available": evaluation_available,
    }


def present_retelling_record(record: RetellingRecord) -> dict:
    return _present_record(record)


def present_sentence_progress(progress: ShadowingSentenceProgress) -> dict:
    return {
        "id": progress.id,
        "resource_id": progress.resource_id,
        "sentence_key": progress.sentence_key,
        "practice_status": progress.practice_status,
        "practice_count": progress.practice_count,
        "updated_at": progress.updated_at,
    }


def _present_record(record: RetellingRecord | None) -> dict:
    if record is None:
        return {
            "id": "",
            "resource_id": "",
            "written_outline": "",
            "intended_vocabulary": (),
            "intended_vocabulary_text": "",
            "retelling_text": "",
            "mistakes": "",
            "improved_version": "",
            "practice_status": "need_practice",
            "active_duration_seconds": 0,
            "perceived_difficulty": None,
            "confidence": None,
            "status": "not_started",
            "submission_revision": 0,
            "started_at": None,
            "submitted_at": None,
            "updated_at": None,
        }
    return {
        "id": record.id,
        "resource_id": record.source_resource_id,
        "written_outline": record.written_outline,
        "intended_vocabulary": record.intended_vocabulary,
        "intended_vocabulary_text": "\n".join(record.intended_vocabulary),
        "retelling_text": record.retelling_text,
        "mistakes": record.mistakes,
        "improved_version": record.improved_version,
        "practice_status": record.practice_status,
        "active_duration_seconds": record.active_duration_seconds,
        "perceived_difficulty": record.perceived_difficulty,
        "confidence": record.confidence,
        "status": record.status,
        "submission_revision": record.submission_revision,
        "started_at": record.started_at,
        "submitted_at": record.submitted_at,
        "updated_at": record.updated_at,
    }
