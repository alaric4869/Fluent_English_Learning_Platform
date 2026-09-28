import json

import pytest
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.routes.practice import get_service, get_services, router
from app.composition import build_application_services
from app.config import FASTAPI_ROOT, settings
from app.content_import import SeedImportError, load_seed_payloads
from app.database import Base
from app.models.ielts import PracticeQuestion, PracticeSet
from app.models.learning_evidence import LearningResource
from app.seed import import_seed_data


def test_manifest_imports_complete_g20_test_1_to_4_catalogue() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        import_seed_data(session, settings.seed_path)
        practice_sets = session.scalars(
            select(PracticeSet).order_by(PracticeSet.test_number, PracticeSet.skill)
        ).all()

        assert len(practice_sets) == 8
        assert all(sum(len(section.questions) for section in item.sections) == 40 for item in practice_sets)
        assert session.scalar(select(func.count()).select_from(LearningResource)) == 25

        map_set = session.scalar(
            select(PracticeSet).where(PracticeSet.slug == "g20-test-3-listening")
        )
        figure = map_set.sections[1].content_blocks[0]
        assert figure["kind"] == "figure"
        assert figure["answer_numbers"] == [17, 18, 19, 20]
        assert (settings.ielts_assets_root / figure["asset_path"]).is_file()

        grouped = session.scalars(
            select(PracticeQuestion)
            .where(PracticeQuestion.practice_set_id == _set_id(session, "g20-test-4-listening"))
            .where(PracticeQuestion.answer_group.is_not(None))
            .order_by(PracticeQuestion.number)
        ).all()
        assert [item.number for item in grouped] == [11, 12, 13, 14, 21, 22, 23, 24]
        assert [item.answer_group for item in grouped] == [
            "stadium-with-children",
            "stadium-with-children",
            "stadium-new-features",
            "stadium-new-features",
            "handwriting-benefits",
            "handwriting-benefits",
            "dyspraxia-problems",
            "dyspraxia-problems",
        ]


def test_test_4_grouped_questions_render_as_two_choice_checkboxes() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        import_seed_data(session, settings.seed_path)
        services = build_application_services(session)
        app = FastAPI()
        app.mount(
            "/static",
            StaticFiles(directory=FASTAPI_ROOT / "app" / "static"),
            name="static",
        )
        app.include_router(router)
        app.dependency_overrides[get_service] = lambda: services.ielts_practice
        app.dependency_overrides[get_services] = lambda: services

        with TestClient(app) as client:
            page = client.get("/ielts/g20-test-4-listening")
            reading_page = client.get("/ielts/g20-test-4-reading")
            map_asset = client.get(
                "/media/ielts-assets/g20/test3/bidcaster-archaeological-dig.png"
            )

        assert page.status_code == 200
        assert reading_page.status_code == 200
        assert 'class="reading-split-layout"' in reading_page.text
        assert 'class="reading-pane reading-source-pane"' in reading_page.text
        assert 'class="reading-pane reading-question-pane"' in reading_page.text
        assert 'data-practice-skill="reading"' in reading_page.text
        assert 'class="reading-split-layout"' not in page.text
        assert 'data-question-numbers="11 12"' in page.text
        assert 'data-max-selections="2"' in page.text
        assert page.text.count('class="group-choice" type="checkbox"') >= 20
        assert "这组题只能选择" in (
            FASTAPI_ROOT / "app" / "static" / "js" / "ielts-practice.js"
        ).read_text(encoding="utf-8")
        assert map_asset.status_code == 200
        assert map_asset.headers["content-type"] == "image/png"


def test_test_one_structured_notes_render_each_answer_once() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        import_seed_data(session, settings.seed_path)
        services = build_application_services(session)
        app = FastAPI()
        app.mount(
            "/static",
            StaticFiles(directory=FASTAPI_ROOT / "app" / "static"),
            name="static",
        )
        app.include_router(router)
        app.dependency_overrides[get_service] = lambda: services.ielts_practice
        app.dependency_overrides[get_services] = lambda: services

        with TestClient(app) as client:
            listening = client.get("/ielts/g20-test-1-listening")
            reading = client.get("/ielts/g20-test-1-reading")

        assert listening.status_code == 200
        assert reading.status_code == 200
        assert "Reclaiming urban rivers" in listening.text
        assert "Creating a successful business" in reading.text
        for number in range(31, 41):
            assert listening.text.count(f'data-answer-number="{number}"') == 1
        for number in range(22, 28):
            assert reading.text.count(f'data-answer-number="{number}"') == 1


def test_manifest_rejects_duplicate_slugs_before_database_writes(tmp_path) -> None:
    payload = {
        "practice_sets": [],
        "learning_resources": [
            {
                "slug": "duplicate-resource",
                "title": "Duplicate",
                "resource_type": "article",
                "skill": "reading",
                "topic": "test",
                "estimated_duration_minutes": 10,
            }
        ],
    }
    (tmp_path / "one.json").write_text(json.dumps(payload), encoding="utf-8")
    (tmp_path / "two.json").write_text(json.dumps(payload), encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps({"schema_version": 1, "imports": ["one.json", "two.json"]}),
        encoding="utf-8",
    )

    with pytest.raises(SeedImportError, match="Duplicate slugs"):
        load_seed_payloads(manifest)


def _set_id(session: Session, slug: str) -> int:
    return session.scalar(select(PracticeSet.id).where(PracticeSet.slug == slug))
