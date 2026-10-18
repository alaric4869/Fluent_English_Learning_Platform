from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.content_import import load_seed_payloads
from app.models.ielts import PracticeQuestion, PracticeSection, PracticeSet
from app.models.learning_evidence import LearningResource


def import_seed_data(session: Session, seed_path: Path) -> None:
    payloads = load_seed_payloads(seed_path)
    for payload in payloads:
        _import_payload(session, payload)
    session.commit()


def _import_payload(session: Session, payload: dict) -> None:
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
    for item in payload.get("learning_resources", []):
        _upsert_standalone_learning_resource(session, item)


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
    resource.priority = payload.get("priority", 50)
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


def _upsert_standalone_learning_resource(session: Session, payload: dict) -> None:
    resource = session.scalar(
        select(LearningResource).where(LearningResource.slug == payload["slug"])
    )
    if resource is None:
        resource = LearningResource(slug=payload["slug"])
        session.add(resource)
    resource.title = payload["title"]
    resource.resource_type = payload["resource_type"]
    resource.skill = payload["skill"]
    resource.topic = payload["topic"]
    resource.difficulty = payload.get("difficulty")
    resource.estimated_duration_minutes = payload["estimated_duration_minutes"]
    resource.source_url = payload.get("source_url")
    resource.local_asset_reference = payload.get("local_asset_reference")
    resource.content = payload.get("content", {})
    resource.tags = payload.get("tags", [])
    resource.priority = payload.get("priority", 50)
    resource.active = payload.get("active", True)
    resource.description = payload.get("description", "")
    resource.content_text = payload.get("content_text", "")
    resource.transcript = payload.get("transcript", "")
    resource.notes = payload.get("notes", "")
