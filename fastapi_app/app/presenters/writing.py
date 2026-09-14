from app.domain.writing.entities import WritingDraft, WritingWorkspace


def present_writing_workspace(workspace: WritingWorkspace) -> dict:
    return {
        "active_page": "ielts",
        "workspace": workspace,
        "draft": _present_draft(workspace.draft),
        "target_progress": min(
            100,
            round((workspace.draft.word_count / workspace.minimum_words) * 100),
        )
        if workspace.draft
        else 0,
    }


def present_writing_draft(draft: WritingDraft) -> dict:
    return {
        "id": draft.id,
        "resource_id": draft.resource_id,
        "response_text": draft.response_text,
        "outline": draft.outline,
        "word_count": draft.word_count,
        "active_duration_seconds": draft.active_duration_seconds,
        "perceived_difficulty": draft.perceived_difficulty,
        "confidence": draft.confidence,
        "status": draft.status,
        "submission_revision": draft.submission_revision,
        "started_at": draft.started_at,
        "submitted_at": draft.submitted_at,
        "updated_at": draft.updated_at,
    }


def _present_draft(draft: WritingDraft | None) -> dict:
    if draft is None:
        return {
            "id": "",
            "response_text": "",
            "outline": "",
            "word_count": 0,
            "active_duration_seconds": 0,
            "perceived_difficulty": None,
            "confidence": None,
            "status": "not_started",
            "submission_revision": 0,
            "submitted_at": None,
        }
    return present_writing_draft(draft)
