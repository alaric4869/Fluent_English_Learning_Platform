from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.frontend_dependencies import get_frontend_services
from app.api.learner_context import Learner
from app.composition import ApplicationServices
from app.domain.listening.entities import ListeningSentenceDraft, ListeningSentenceStatus
from app.domain.notebook.entities import NoteDraft, NoteType
from app.domain.speaking.entities import RetellingDraft, SpeakingPracticeStatus
from app.schemas.frontend_notebook import (
    NotebookCountsResponse,
    NotebookNoteItemResponse,
    NotebookResponse,
    NotebookRetellingItemResponse,
    NotebookSentenceItemResponse,
)
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


router = APIRouter(prefix="/api/v1/notebook", tags=["frontend-notebook"])
SYDNEY = ZoneInfo("Australia/Sydney")
NOTE_LABELS = {
    NoteType.VOCABULARY: "词汇",
    NoteType.USEFUL_EXPRESSION: "实用表达",
    NoteType.LISTENING_MISTAKE: "听力错误",
    NoteType.PRONUNCIATION: "发音问题",
    NoteType.GRAMMAR: "语法错误",
    NoteType.SPEAKING_MISTAKE: "口语错误",
    NoteType.SENTENCE: "想记住的句子",
}
SENTENCE_LABELS = {
    ListeningSentenceStatus.COULD_NOT_HEAR: "听不清",
    ListeningSentenceStatus.DIFFICULT: "困难",
    ListeningSentenceStatus.UNDERSTOOD: "已理解",
    ListeningSentenceStatus.MASTERED: "已掌握",
}
RETELLING_LABELS = {
    SpeakingPracticeStatus.NEED_PRACTICE: "需要练习",
    SpeakingPracticeStatus.GOOD: "不错",
    SpeakingPracticeStatus.MASTERED: "已掌握",
}


@router.get("", response_model=NotebookResponse)
def get_notebook(
    learner: Learner,
    search: str = "",
    note_type: str = "",
    sentence_status: str = "",
    services: ApplicationServices = Depends(get_frontend_services),
) -> NotebookResponse:
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
    return NotebookResponse(
        counts=NotebookCountsResponse(
            notes=len(notes),
            sentences=len(sentences),
            retellings=len(retellings),
        ),
        notes=[
            NotebookNoteItemResponse(
                id=item.id,
                note_type=item.note_type.value,
                type_label=NOTE_LABELS[item.note_type],
                title=item.title,
                content=item.content,
                source_context=item.source_context,
                tags=list(item.tags),
                favorite=item.favorite,
                saved_for_later=item.saved_for_later,
                created_at=item.created_at,
            )
            for item in notes
        ],
        sentences=[_sentence_item(item) for item in sentences],
        retellings=[
            NotebookRetellingItemResponse(
                id=item.id,
                prompt=item.prompt,
                written_outline=item.written_outline,
                intended_vocabulary=list(item.intended_vocabulary),
                retelling_text=item.retelling_text,
                mistakes=item.mistakes,
                improved_version=item.improved_version,
                practice_status=item.practice_status.value,
                status_label=RETELLING_LABELS[item.practice_status],
                source_context=item.source_context,
                created_at=item.created_at,
            )
            for item in retellings
        ],
    )


@router.post(
    "/notes",
    response_model=NotebookNoteResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_note(
    payload: NotebookNoteCreateRequest,
    learner: Learner,
    services: ApplicationServices = Depends(get_frontend_services),
) -> NotebookNoteResponse:
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
    return NotebookNoteResponse(
        id=note.id,
        note_type=note.note_type,
        title=note.title,
        content=note.content,
        source_context=note.source_context,
        tags=list(note.tags),
        favorite=note.favorite,
        saved_for_later=note.saved_for_later,
        created_at=note.created_at,
    )


@router.post(
    "/sentences",
    response_model=ListeningSentenceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_sentence(
    payload: ListeningSentenceCreateRequest,
    learner: Learner,
    services: ApplicationServices = Depends(get_frontend_services),
) -> ListeningSentenceResponse:
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
    return _sentence_response(item)


@router.patch(
    "/sentences/{sentence_id}/status",
    response_model=ListeningSentenceResponse,
)
def update_sentence_status(
    sentence_id: int,
    payload: ListeningSentenceStatusRequest,
    learner: Learner,
    services: ApplicationServices = Depends(get_frontend_services),
) -> ListeningSentenceResponse:
    try:
        item = services.listening.update_status(
            learner.user_key, sentence_id, payload.practice_status
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return _sentence_response(item)


@router.post(
    "/retellings",
    response_model=RetellingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_retelling(
    payload: RetellingCreateRequest,
    learner: Learner,
    services: ApplicationServices = Depends(get_frontend_services),
) -> RetellingResponse:
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
            ),
        )
    except InvalidRetellingError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return RetellingResponse(
        id=item.id,
        prompt=item.prompt,
        written_outline=item.written_outline,
        intended_vocabulary=list(item.intended_vocabulary),
        mistakes=item.mistakes,
        improved_version=item.improved_version,
        practice_status=item.practice_status,
        source_context=item.source_context,
        voice_recording_reference=item.voice_recording_reference,
        created_at=item.created_at,
    )


def _sentence_item(item) -> NotebookSentenceItemResponse:
    return NotebookSentenceItemResponse(
        id=item.id,
        sentence=item.sentence,
        meaning=item.meaning,
        learned_on=item.learned_on,
        practice_status=item.practice_status.value,
        status_label=SENTENCE_LABELS[item.practice_status],
        note=item.note,
        source_context=item.source_context,
        review_item_id=item.review_item_id,
        next_review_date=item.next_review_date,
        review_count=item.review_count,
        mastery_status=item.mastery_status.value if item.mastery_status else None,
    )


def _sentence_response(item) -> ListeningSentenceResponse:
    return ListeningSentenceResponse(
        id=item.id,
        sentence=item.sentence,
        meaning=item.meaning,
        learned_on=item.learned_on,
        practice_status=item.practice_status,
        note=item.note,
        source_context=item.source_context,
        review_item_id=item.review_item_id,
        next_review_date=item.next_review_date,
        review_count=item.review_count,
        mastery_status=item.mastery_status,
    )
