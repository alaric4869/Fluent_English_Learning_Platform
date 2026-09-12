import json
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.ielts import PracticeAttempt, PracticeQuestion, PracticeSection, PracticeSet


def import_seed_data(session: Session, seed_path: Path) -> None:
    payload = json.loads(seed_path.read_text(encoding="utf-8"))
    for item in payload["practice_sets"]:
        existing = session.scalar(select(PracticeSet).where(PracticeSet.slug == item["slug"]))
        if existing and existing.content_version == item["content_version"]:
            continue
        if existing:
            session.execute(delete(PracticeAttempt).where(PracticeAttempt.practice_set_id == existing.id))
            session.delete(existing)
            session.flush()

        practice_set = PracticeSet(
            slug=item["slug"],
            book_number=item["book_number"],
            test_number=item["test_number"],
            skill=item["skill"],
            title=item["title"],
            description=item["description"],
            duration_minutes=item["duration_minutes"],
            content_version=item["content_version"],
        )
        session.add(practice_set)
        session.flush()
        for section_payload in item["sections"]:
            section = PracticeSection(
                practice_set_id=practice_set.id,
                order_index=section_payload["order_index"],
                title=section_payload["title"],
                instructions=section_payload["instructions"],
                content_blocks=section_payload.get("content_blocks", []),
                audio_path=section_payload.get("audio_path"),
            )
            session.add(section)
            session.flush()
            for question_payload in section_payload["questions"]:
                session.add(
                    PracticeQuestion(
                        practice_set_id=practice_set.id,
                        section_id=section.id,
                        number=question_payload["number"],
                        prompt=question_payload["prompt"],
                        question_type=question_payload["question_type"],
                        options=question_payload.get("options", []),
                        accepted_answers=question_payload["accepted_answers"],
                        answer_group=question_payload.get("answer_group"),
                        explanation=question_payload["explanation"],
                    )
                )
    session.commit()

