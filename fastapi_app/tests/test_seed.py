import json

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.database import Base
from app.models.ielts import PracticeAttempt, PracticeQuestion, PracticeSet
from app.models.learning_evidence import LearningResource
from app.seed import import_seed_data


def test_content_update_preserves_existing_attempt(tmp_path) -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    seed_path = tmp_path / "seed.json"
    payload = _seed_payload("version-1", "Original prompt")
    seed_path.write_text(json.dumps(payload), encoding="utf-8")

    with Session(engine) as session:
        import_seed_data(session, seed_path)
        practice_set = session.scalar(select(PracticeSet))
        session.add(
            PracticeAttempt(
                practice_set_id=practice_set.id,
                user_key="learner",
                answers={"1": "saved answer"},
            )
        )
        session.commit()
        original_set_id = practice_set.id

    payload = _seed_payload("version-2", "Updated prompt")
    seed_path.write_text(json.dumps(payload), encoding="utf-8")
    with Session(engine) as session:
        import_seed_data(session, seed_path)
        practice_set = session.scalar(select(PracticeSet))
        attempt = session.scalar(select(PracticeAttempt))
        question = session.scalar(select(PracticeQuestion))
        resource = session.scalar(select(LearningResource))

        assert practice_set.id == original_set_id
        assert practice_set.learning_resource_id == resource.id
        assert practice_set.content_version == "version-2"
        assert attempt.answers == {"1": "saved answer"}
        assert question.prompt == "Updated prompt"
        assert resource.skill == "listening"
        assert resource.resource_type == "ielts_listening"


def _seed_payload(version: str, prompt: str) -> dict:
    return {
        "practice_sets": [
            {
                "slug": "safe-seed",
                "book_number": 20,
                "test_number": 1,
                "skill": "listening",
                "title": "Safe seed",
                "description": "Test data",
                "duration_minutes": 30,
                "content_version": version,
                "sections": [
                    {
                        "order_index": 1,
                        "title": "Part 1",
                        "instructions": "Answer the question.",
                        "content_blocks": [],
                        "questions": [
                            {
                                "number": 1,
                                "prompt": prompt,
                                "question_type": "text",
                                "accepted_answers": ["answer"],
                                "explanation": "Explanation",
                            }
                        ],
                    }
                ],
            }
        ]
    }
