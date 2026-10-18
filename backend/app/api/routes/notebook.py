from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.learner_context import Learner
from app.composition import ApplicationServices, build_application_services
from app.config import FASTAPI_ROOT
from app.database import get_db
from app.domain.listening.entities import ListeningSentenceDraft, ListeningSentenceStatus
from app.domain.notebook.entities import NoteDraft, NoteType
from app.domain.speaking.entities import RetellingDraft
from app.presenters.notebook import present_notebook_page
from app.schemas.notebook import (
    ListeningSentenceCreateRequest,
    ListeningSentenceResponse,
    ListeningSentenceStatusRequest,
    NotebookNoteCreateRequest,
    NotebookNoteResponse,
    RetellingCreateRequest,
    RetellingResponse,
)
from app.services.listening import InvalidListeningSentenceError
from app.services.notebook import InvalidNoteError
from app.services.speaking import InvalidRetellingError


router = APIRouter()
templates = Jinja2Templates(directory=FASTAPI_ROOT / "app" / "templates")
SYDNEY = ZoneInfo("Australia/Sydney")


def get_services(session: Session = Depends(get_db)) -> ApplicationServices:
    return build_application_services(session)


@router.get("/notebook")
def notebook_page(
    request: Request,
    learner: Learner,
    view: str = "notes",
    search: str = "",
    note_type: str = "",
    sentence_status: str = "",
    services: ApplicationServices = Depends(get_services),
):
    if view not in {"notes", "listening", "speaking"}:
        view = "notes"
    try:
        selected_note_type = NoteType(note_type) if note_type else None
        selected_sentence_status = (
            ListeningSentenceStatus(sentence_status) if sentence_status else None
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail="Invalid notebook filter") from error
    notes = services.notebook.get_notes(
        learner.user_key, search=search, note_type=selected_note_type
    )
    sentences = services.listening.list_sentences(
        learner.user_key, search=search, status=selected_sentence_status
    )
    retellings = services.speaking.list_retellings(learner.user_key, search=search)
    return templates.TemplateResponse(
        request=request,
        name="notebook/index.html",
        context=present_notebook_page(
            view=view,
            search=search,
            selected_note_type=selected_note_type,
            selected_sentence_status=selected_sentence_status,
            notes=notes,
            sentences=sentences,
            retellings=retellings,
        ),
    )


@router.post(
    "/api/notebook/notes",
    response_model=NotebookNoteResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_note(
    payload: NotebookNoteCreateRequest,
    learner: Learner,
    services: ApplicationServices = Depends(get_services),
):
    try:
        note = services.notebook.add_note(
            learner.user_key,
            NoteDraft(
                note_type=payload.note_type,
                title=payload.title,
                content=payload.content,
                source_resource_id=payload.source_resource_id,
                source_context=payload.source_context,
                tags=tuple(payload.tags),
            ),
        )
    except InvalidNoteError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return _present_note(note)


@router.post(
    "/api/listening/sentences",
    response_model=ListeningSentenceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_listening_sentence(
    payload: ListeningSentenceCreateRequest,
    learner: Learner,
    services: ApplicationServices = Depends(get_services),
):
    today = datetime.now(SYDNEY).date()
    try:
        item = services.listening.save_sentence(
            learner.user_key,
            ListeningSentenceDraft(
                sentence=payload.sentence,
                meaning=payload.meaning,
                learned_on=payload.learned_on or today,
                practice_status=payload.practice_status,
                note=payload.note,
                source_resource_id=payload.source_resource_id,
                source_context=payload.source_context,
                add_to_review=payload.add_to_review,
            ),
            today,
        )
    except InvalidListeningSentenceError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return _present_sentence(item)


@router.patch(
    "/api/listening/sentences/{sentence_id}/status",
    response_model=ListeningSentenceResponse,
)
def update_listening_sentence_status(
    sentence_id: int,
    payload: ListeningSentenceStatusRequest,
    learner: Learner,
    services: ApplicationServices = Depends(get_services),
):
    try:
        item = services.listening.update_status(
            learner.user_key, sentence_id, payload.practice_status
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return _present_sentence(item)


@router.post(
    "/api/speaking/retellings",
    response_model=RetellingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_retelling(
    payload: RetellingCreateRequest,
    learner: Learner,
    services: ApplicationServices = Depends(get_services),
):
    try:
        item = services.speaking.save_retelling(
            learner.user_key,
            RetellingDraft(
                prompt=payload.prompt,
                written_outline=payload.written_outline,
                intended_vocabulary=tuple(payload.intended_vocabulary),
                mistakes=payload.mistakes,
                improved_version=payload.improved_version,
                practice_status=payload.practice_status,
                source_resource_id=payload.source_resource_id,
                source_context=payload.source_context,
                voice_recording_reference=None,
            ),
        )
    except InvalidRetellingError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return _present_retelling(item)


def _present_note(note) -> dict:
    return {
        "id": note.id,
        "note_type": note.note_type,
        "title": note.title,
        "content": note.content,
        "source_context": note.source_context,
        "tags": list(note.tags),
        "favorite": note.favorite,
        "saved_for_later": note.saved_for_later,
        "created_at": note.created_at,
    }


def _present_sentence(item) -> dict:
    return {
        "id": item.id,
        "sentence": item.sentence,
        "meaning": item.meaning,
        "learned_on": item.learned_on,
        "practice_status": item.practice_status,
        "note": item.note,
        "source_context": item.source_context,
        "review_item_id": item.review_item_id,
        "next_review_date": item.next_review_date,
        "review_count": item.review_count,
        "mastery_status": item.mastery_status,
    }


def _present_retelling(item) -> dict:
    return {
        "id": item.id,
        "prompt": item.prompt,
        "written_outline": item.written_outline,
        "intended_vocabulary": list(item.intended_vocabulary),
        "mistakes": item.mistakes,
        "improved_version": item.improved_version,
        "practice_status": item.practice_status,
        "source_context": item.source_context,
        "voice_recording_reference": item.voice_recording_reference,
        "created_at": item.created_at,
    }
