from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.frontend_dependencies import get_frontend_services
from app.api.learner_context import Learner
from app.composition import ApplicationServices
from app.domain.speaking.entities import RetellingWorkspaceInput
from app.domain.writing.entities import WritingDraftInput
from app.presenters.listening import present_listening_workspace
from app.presenters.speaking import present_retelling_record, present_sentence_progress
from app.presenters.writing import present_writing_draft
from app.schemas.frontend_practice import (
    ListeningWorkspaceResponse,
    SpeakingDraftStateResponse,
    SpeakingWorkspaceResponse,
    WritingDraftStateResponse,
    WritingWorkspaceResponse,
)
from app.schemas.listening import TranscriptSentenceMarkRequest
from app.schemas.notebook import ListeningSentenceResponse as SavedListeningSentenceResponse
from app.schemas.speaking import (
    SpeakingDraftRequest,
    SpeakingDraftResponse,
    SpeakingSentenceProgressResponse,
    SpeakingSentenceStatusRequest,
    SpeakingSubmissionResponse,
)
from app.schemas.writing import WritingDraftRequest, WritingDraftResponse, WritingSubmissionResponse
from app.services.listening import InvalidListeningSentenceError
from app.services.speaking import IncompleteRetellingError, InvalidRetellingError
from app.services.writing import IncompleteWritingDraftError, InvalidWritingDraftError


router = APIRouter(prefix="/api/v1", tags=["frontend-practice"])
SYDNEY = ZoneInfo("Australia/Sydney")


@router.get("/writing/{resource_id}", response_model=WritingWorkspaceResponse)
def get_writing_workspace(
    resource_id: int,
    learner: Learner,
    services: ApplicationServices = Depends(get_frontend_services),
) -> WritingWorkspaceResponse:
    try:
        workspace = services.writing.get_workspace(learner.user_key, resource_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidWritingDraftError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    draft = workspace.draft
    return WritingWorkspaceResponse(
        resource_id=workspace.resource.id,
        resource_title=workspace.resource.title,
        description=workspace.resource.description,
        test_number=int(workspace.resource.content.get("test_number", 1)),
        minimum_words=workspace.minimum_words,
        recommended_minutes=workspace.recommended_minutes,
        task_type=workspace.task_type,
        instructions=workspace.instructions,
        situation=workspace.situation,
        prompt=workspace.prompt,
        bullet_points=list(workspace.bullet_points),
        closing_instruction=workspace.closing_instruction,
        draft=WritingDraftStateResponse(
            id=draft.id if draft else None,
            resource_id=workspace.resource.id,
            response_text=draft.response_text if draft else "",
            outline=draft.outline if draft else "",
            word_count=draft.word_count if draft else 0,
            active_duration_seconds=draft.active_duration_seconds if draft else 0,
            perceived_difficulty=draft.perceived_difficulty if draft else None,
            confidence=draft.confidence if draft else None,
            status=draft.status.value if draft else "not_started",
            submission_revision=draft.submission_revision if draft else 0,
            started_at=draft.started_at if draft else None,
            submitted_at=draft.submitted_at if draft else None,
            updated_at=draft.updated_at if draft else None,
        ),
    )


@router.put("/writing/{resource_id}/draft", response_model=WritingDraftResponse)
def save_writing_draft(
    resource_id: int,
    payload: WritingDraftRequest,
    learner: Learner,
    services: ApplicationServices = Depends(get_frontend_services),
):
    try:
        draft = services.writing.save_draft(
            learner.user_key,
            resource_id,
            WritingDraftInput(**payload.model_dump()),
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidWritingDraftError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return present_writing_draft(draft)


@router.post("/writing/{resource_id}/submit", response_model=WritingSubmissionResponse)
def submit_writing(
    resource_id: int,
    learner: Learner,
    services: ApplicationServices = Depends(get_frontend_services),
):
    try:
        draft, submission, study_session_id = services.writing.submit(learner.user_key, resource_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except IncompleteWritingDraftError as error:
        raise HTTPException(status_code=422, detail={"message": str(error), "word_count": error.word_count, "minimum_words": error.minimum_words}) from error
    except InvalidWritingDraftError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"draft": present_writing_draft(draft), "submission_id": submission.id, "submission_revision": submission.revision, "study_session_id": study_session_id, "word_count": submission.word_count, "submitted_at": submission.submitted_at, "created": submission.created}


@router.get("/speaking/{resource_id}", response_model=SpeakingWorkspaceResponse)
def get_speaking_workspace(
    resource_id: int,
    learner: Learner,
    services: ApplicationServices = Depends(get_frontend_services),
) -> SpeakingWorkspaceResponse:
    try:
        workspace = services.speaking.get_workspace(learner.user_key, resource_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidRetellingError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    record = workspace.record
    return SpeakingWorkspaceResponse(
        resource_id=workspace.resource.id,
        resource_title=workspace.resource.title,
        description=workspace.resource.description,
        test_number=int(workspace.resource.content.get("test_number", 1)),
        estimated_duration_minutes=workspace.resource.estimated_duration_minutes,
        audio_url=workspace.audio_url,
        source_label=workspace.source_label,
        context=workspace.context,
        workflow=list(workspace.workflow),
        sentences=[{
            "key": sentence.key,
            "speaker": sentence.speaker,
            "text": sentence.text,
            "pronunciation_note": sentence.pronunciation_note,
            "connected_speech_note": sentence.connected_speech_note,
            "chunks": list(sentence.chunks),
            "progress": ({
                "practice_status": sentence.progress.practice_status.value,
                "practice_count": sentence.progress.practice_count,
                "updated_at": sentence.progress.updated_at,
            } if sentence.progress else None),
        } for sentence in workspace.sentences],
        retelling_prompt=workspace.retelling_prompt,
        retelling_guidance=list(workspace.retelling_guidance),
        marked_count=sum(sentence.progress is not None for sentence in workspace.sentences),
        mastered_count=sum(sentence.progress is not None and sentence.progress.practice_status.value == "mastered" for sentence in workspace.sentences),
        draft=SpeakingDraftStateResponse(
            id=record.id if record else None,
            resource_id=workspace.resource.id,
            written_outline=record.written_outline if record else "",
            intended_vocabulary=list(record.intended_vocabulary) if record else [],
            retelling_text=record.retelling_text if record else "",
            mistakes=record.mistakes if record else "",
            improved_version=record.improved_version if record else "",
            practice_status=record.practice_status.value if record else "need_practice",
            active_duration_seconds=record.active_duration_seconds if record else 0,
            perceived_difficulty=record.perceived_difficulty if record else None,
            confidence=record.confidence if record else None,
            status=record.status.value if record else "not_started",
            submission_revision=record.submission_revision if record else 0,
            started_at=record.started_at if record else None,
            submitted_at=record.submitted_at if record else None,
            updated_at=record.updated_at if record else None,
        ),
    )


@router.put("/speaking/{resource_id}/draft", response_model=SpeakingDraftResponse)
def save_speaking_draft(resource_id: int, payload: SpeakingDraftRequest, learner: Learner, services: ApplicationServices = Depends(get_frontend_services)):
    try:
        record = services.speaking.save_workspace_draft(learner.user_key, resource_id, RetellingWorkspaceInput(written_outline=payload.written_outline, intended_vocabulary=tuple(payload.intended_vocabulary), retelling_text=payload.retelling_text, mistakes=payload.mistakes, improved_version=payload.improved_version, practice_status=payload.practice_status, active_duration_seconds=payload.active_duration_seconds, perceived_difficulty=payload.perceived_difficulty, confidence=payload.confidence))
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidRetellingError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return present_retelling_record(record)


@router.put("/speaking/{resource_id}/sentences/{sentence_key}", response_model=SpeakingSentenceProgressResponse)
def mark_speaking_sentence(resource_id: int, sentence_key: str, payload: SpeakingSentenceStatusRequest, learner: Learner, services: ApplicationServices = Depends(get_frontend_services)):
    try:
        return present_sentence_progress(services.speaking.mark_sentence(learner.user_key, resource_id, sentence_key, payload.practice_status))
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidRetellingError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/speaking/{resource_id}/submit", response_model=SpeakingSubmissionResponse)
def submit_speaking(resource_id: int, learner: Learner, services: ApplicationServices = Depends(get_frontend_services)):
    try:
        record, submission, study_session_id = services.speaking.submit(learner.user_key, resource_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except (IncompleteRetellingError, InvalidRetellingError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"draft": present_retelling_record(record), "submission_id": submission.id, "submission_revision": submission.revision, "study_session_id": study_session_id, "submitted_at": submission.submitted_at, "created": submission.created}


@router.get("/listening/{resource_id}", response_model=ListeningWorkspaceResponse)
def get_listening_workspace(resource_id: int, learner: Learner, services: ApplicationServices = Depends(get_frontend_services)) -> ListeningWorkspaceResponse:
    resource = services.resources.get_user_resource(learner.user_key, resource_id)
    if resource is None:
        raise HTTPException(status_code=404, detail="Listening resource not found")
    try:
        saved = services.listening.list_for_resource(learner.user_key, resource_id)
    except InvalidListeningSentenceError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    presented = present_listening_workspace(resource, saved)
    media_kind = "missing"
    media_url = None
    if presented["youtube_embed_url"]:
        media_kind, media_url = "youtube", presented["youtube_embed_url"]
    elif presented["direct_audio_url"]:
        media_kind, media_url = "audio", presented["direct_audio_url"]
    elif presented["local_audio_parts"]:
        media_kind = "local_parts"
    elif presented["external_url"]:
        media_kind, media_url = "external", presented["external_url"]
    return ListeningWorkspaceResponse(
        resource_id=resource.id, title=resource.title, description=resource.description,
        topic=resource.topic, difficulty=resource.difficulty, resource_type=resource.resource_type,
        estimated_duration_minutes=resource.estimated_duration_minutes, is_user_owned=resource.is_user_owned,
        media_kind=media_kind, media_url=media_url, local_audio_parts=list(presented["local_audio_parts"]),
        practice_href=presented["practice_href"],
        sentences=[{
            "position": item["position"], "text": item["text"], "status": item["status"],
            "saved_id": item["saved"].id if item["saved"] else None,
            "review_item_id": item["saved"].review_item_id if item["saved"] else None,
            "next_review_date": str(item["saved"].next_review_date) if item["saved"] and item["saved"].next_review_date else None,
        } for item in presented["sentences"]],
    )


@router.post("/listening/{resource_id}/sentences", response_model=SavedListeningSentenceResponse, status_code=status.HTTP_200_OK)
def mark_listening_sentence(resource_id: int, payload: TranscriptSentenceMarkRequest, learner: Learner, services: ApplicationServices = Depends(get_frontend_services)):
    try:
        item = services.listening.mark_transcript_sentence(learner.user_key, resource_id, payload.sentence, payload.practice_status, datetime.now(SYDNEY).date())
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidListeningSentenceError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"id": item.id, "sentence": item.sentence, "meaning": item.meaning, "learned_on": item.learned_on, "practice_status": item.practice_status, "note": item.note, "source_context": item.source_context, "review_item_id": item.review_item_id, "next_review_date": item.next_review_date, "review_count": item.review_count, "mastery_status": item.mastery_status}
