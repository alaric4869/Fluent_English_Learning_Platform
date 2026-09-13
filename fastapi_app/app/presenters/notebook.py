from app.domain.listening.entities import ListeningSentenceStatus, SavedListeningSentence
from app.domain.notebook.entities import NotebookNote, NoteType
from app.domain.speaking.entities import RetellingRecord, SpeakingPracticeStatus


NOTE_TYPE_LABELS = {
    NoteType.VOCABULARY: "词汇",
    NoteType.USEFUL_EXPRESSION: "实用表达",
    NoteType.LISTENING_MISTAKE: "听力错误",
    NoteType.PRONUNCIATION: "发音问题",
    NoteType.GRAMMAR: "语法错误",
    NoteType.SPEAKING_MISTAKE: "口语错误",
    NoteType.SENTENCE: "想记住的句子",
}
SENTENCE_STATUS_LABELS = {
    ListeningSentenceStatus.COULD_NOT_HEAR: "听不清",
    ListeningSentenceStatus.DIFFICULT: "困难",
    ListeningSentenceStatus.UNDERSTOOD: "已理解",
    ListeningSentenceStatus.MASTERED: "已掌握",
}
SPEAKING_STATUS_LABELS = {
    SpeakingPracticeStatus.NEED_PRACTICE: "需要练习",
    SpeakingPracticeStatus.GOOD: "不错",
    SpeakingPracticeStatus.MASTERED: "已掌握",
}


def present_notebook_page(
    *,
    view: str,
    search: str,
    selected_note_type: NoteType | None,
    selected_sentence_status: ListeningSentenceStatus | None,
    notes: tuple[NotebookNote, ...],
    sentences: tuple[SavedListeningSentence, ...],
    retellings: tuple[RetellingRecord, ...],
) -> dict:
    return {
        "active_page": "notebook",
        "view": view,
        "search": search,
        "selected_note_type": selected_note_type.value if selected_note_type else "",
        "selected_sentence_status": (
            selected_sentence_status.value if selected_sentence_status else ""
        ),
        "note_type_options": tuple(
            (value.value, label) for value, label in NOTE_TYPE_LABELS.items()
        ),
        "sentence_status_options": tuple(
            (value.value, label) for value, label in SENTENCE_STATUS_LABELS.items()
        ),
        "speaking_status_options": tuple(
            (value.value, label) for value, label in SPEAKING_STATUS_LABELS.items()
        ),
        "notes": tuple(
            {"item": item, "type_label": NOTE_TYPE_LABELS[item.note_type]}
            for item in notes
        ),
        "sentences": tuple(
            {
                "item": item,
                "status_label": SENTENCE_STATUS_LABELS[item.practice_status],
            }
            for item in sentences
        ),
        "retellings": tuple(
            {
                "item": item,
                "status_label": SPEAKING_STATUS_LABELS[item.practice_status],
            }
            for item in retellings
        ),
        "counts": {
            "notes": len(notes),
            "sentences": len(sentences),
            "retellings": len(retellings),
        },
    }
