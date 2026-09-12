import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ielts import PracticeQuestion, PracticeSection, PracticeSet
from app.models.learning_evidence import LearningResource


def import_seed_data(session: Session, seed_path: Path) -> None:
    payload = json.loads(seed_path.read_text(encoding="utf-8"))
    for item in payload["practice_sets"]:
        learning_resource = _upsert_learning_resource(session, item)
        existing = session.scalar(select(PracticeSet).where(PracticeSet.slug == item["slug"]))
        if existing is not None and existing.learning_resource_id != learning_resource.id:
            existing.learning_resource_id = learning_resource.id
        if existing and existing.content_version == item["content_version"]:
            continue
        practice_set = existing or PracticeSet(slug=item["slug"])
        _update_practice_set(practice_set, item)
        practice_set.learning_resource_id = learning_resource.id
        if existing is None:
            session.add(practice_set)
            session.flush()

        sections_by_order = {section.order_index: section for section in practice_set.sections}
        questions_by_number = {
            question.number: question
            for section in practice_set.sections
            for question in section.questions
        }
        for section_payload in item["sections"]:
            order_index = section_payload["order_index"]
            section = sections_by_order.get(order_index)
            if section is None:
                section = PracticeSection(practice_set_id=practice_set.id, order_index=order_index)
                _update_section(section, section_payload)
                session.add(section)
                session.flush()
                sections_by_order[order_index] = section
            else:
                _update_section(section, section_payload)

            for question_payload in section_payload["questions"]:
                number = question_payload["number"]
                question = questions_by_number.get(number)
                if question is None:
                    question = PracticeQuestion(practice_set_id=practice_set.id, number=number)
                    session.add(question)
                    questions_by_number[number] = question
                _update_question(question, section, question_payload)
    session.commit()


def _upsert_learning_resource(session: Session, payload: dict) -> LearningResource:
    resource = session.scalar(
        select(LearningResource).where(LearningResource.slug == payload["slug"])
    )
    is_new = resource is None
    if resource is None:
        resource = LearningResource(slug=payload["slug"])
    skill = payload["skill"]
    resource.title = payload["title"]
    resource.resource_type = payload.get("resource_type", f"ielts_{skill}")
    resource.skill = skill
    resource.topic = payload.get("topic", "IELTS General Training")
    resource.difficulty = payload.get("difficulty", "intermediate")
    resource.estimated_duration_minutes = payload["duration_minutes"]
    resource.source_url = payload.get("source_url")
    resource.local_asset_reference = payload.get("local_asset_reference")
    resource.content = {
        "practice_set_slug": payload["slug"],
        "book_number": payload["book_number"],
        "test_number": payload["test_number"],
    }
    resource.tags = payload.get(
        "tags",
        ["ielts", "general-training", f"g{payload['book_number']}", skill],
    )
    resource.active = True
    if is_new:
        session.add(resource)
        session.flush()
    return resource


def _update_practice_set(practice_set: PracticeSet, payload: dict) -> None:
    practice_set.book_number = payload["book_number"]
    practice_set.test_number = payload["test_number"]
    practice_set.skill = payload["skill"]
    practice_set.title = payload["title"]
    practice_set.description = payload["description"]
    practice_set.duration_minutes = payload["duration_minutes"]
    practice_set.content_version = payload["content_version"]


def _update_section(section: PracticeSection, payload: dict) -> None:
    section.title = payload["title"]
    section.instructions = payload["instructions"]
    section.content_blocks = payload.get("content_blocks", [])
    section.audio_path = payload.get("audio_path")


def _update_question(
    question: PracticeQuestion,
    section: PracticeSection,
    payload: dict,
) -> None:
    question.section_id = section.id
    question.prompt = payload["prompt"]
    question.question_type = payload["question_type"]
    question.options = payload.get("options", [])
    question.accepted_answers = payload["accepted_answers"]
    question.answer_group = payload.get("answer_group")
    question.explanation = payload["explanation"]
