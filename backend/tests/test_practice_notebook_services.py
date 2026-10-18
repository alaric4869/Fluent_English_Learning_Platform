from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.composition import build_application_services
from app.database import Base
from app.domain.listening.entities import ListeningSentenceDraft, ListeningSentenceStatus
from app.domain.notebook.entities import NoteDraft, NoteType
from app.domain.review.entities import ReviewRating, ReviewTargetType
from app.domain.speaking.entities import RetellingDraft, SpeakingPracticeStatus


TODAY = date(2026, 9, 13)


def test_listening_sentence_uses_generic_review_queue_and_can_change_status() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        services = build_application_services(session)
        sentence = services.listening.save_sentence(
            "learner",
            ListeningSentenceDraft(
                sentence=" Did you want me to book that in for next Thursday? ",
                meaning="你想让我替你预约到下周四吗？",
                learned_on=date(2026, 9, 12),
                practice_status=ListeningSentenceStatus.COULD_NOT_HEAR,
                note="want me to 连读",
                source_context="Reception conversation",
                add_to_review=True,
            ),
            TODAY,
        )

        due = services.review.get_due_reviews("learner", TODAY)
        assert len(due) == 1
        assert due[0].target_type is ReviewTargetType.SAVED_SENTENCE
        assert due[0].target_id == sentence.id

        reviewed = services.review.record_review(
            "learner",
            sentence.review_item_id,
            ReviewRating.GOOD,
            TODAY,
            "c2afe775-1121-4ba1-a0b7-ca0059a0edca",
        )
        updated = services.listening.update_status(
            "learner", sentence.id, ListeningSentenceStatus.UNDERSTOOD
        )

        assert reviewed.vocabulary_item_id is None
        assert reviewed.saved_sentence_id == sentence.id
        assert reviewed.target_type is ReviewTargetType.SAVED_SENTENCE
        assert reviewed.next_review_date == date(2026, 9, 15)
        assert updated.practice_status is ListeningSentenceStatus.UNDERSTOOD
        assert updated.review_count == 1


def test_notebook_and_retelling_records_are_searchable_and_keep_future_voice_field() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        services = build_application_services(session)
        services.notebook.add_note(
            "learner",
            NoteDraft(
                note_type=NoteType.GRAMMAR,
                title="Past tense endings",
                content="I omitted -ed while retelling.",
                source_context="Test 1 speaking",
                tags=("grammar", "retelling", "grammar"),
            ),
        )
        record = services.speaking.save_retelling(
            "learner",
            RetellingDraft(
                prompt="Retell the reception conversation.",
                written_outline="call → change appointment → confirm",
                intended_vocabulary=("reschedule an appointment", "in the end"),
                mistakes="Used change instead of reschedule.",
                improved_version="She called to reschedule her appointment.",
                practice_status=SpeakingPracticeStatus.NEED_PRACTICE,
                source_context="Reception conversation",
                voice_recording_reference=None,
            ),
        )

        notes = services.notebook.get_notes(
            "learner", search="omitted", note_type=NoteType.GRAMMAR
        )
        retellings = services.speaking.list_retellings(
            "learner", search="reschedule"
        )

        assert len(notes) == 1
        assert notes[0].tags == ("grammar", "retelling")
        assert len(retellings) == 1
        assert retellings[0].id == record.id
        assert retellings[0].voice_recording_reference is None
