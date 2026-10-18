from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.frontend_dependencies import get_frontend_services
from app.api.routes.frontend_ielts import router
from app.composition import build_application_services
from app.config import settings
from app.database import Base
from app.seed import import_seed_data


def test_react_ielts_contract_preserves_layout_without_exposing_answers() -> None:
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
        app.include_router(router)
        app.dependency_overrides[get_frontend_services] = lambda: services

        with TestClient(app) as client:
            catalog = client.get("/api/v1/ielts")
            listening = client.get("/api/v1/ielts/g20-test-1-listening")
            reading = client.get("/api/v1/ielts/g20-test-1-reading")
            map_workspace = client.get("/api/v1/ielts/g20-test-3-listening")

    assert catalog.status_code == 200
    assert catalog.json()["module_count"] == 17
    assert sum(item["migrated"] for item in catalog.json()["modules"]) == 17

    assert listening.status_code == 200
    listening_payload = listening.json()
    assert listening_payload["question_count"] == 40
    assert listening_payload["sections"][0]["content_blocks"][0]["kind"] == "table"
    assert listening_payload["sections"][0]["content_blocks"][0]["rows"][0]["cells"]
    assert "accepted_answers" not in listening.text
    assert "explanation" not in listening.text

    assert reading.status_code == 200
    reading_section = reading.json()["sections"][0]
    assert reading_section["source_blocks"]
    assert reading_section["question_blocks"] == []

    assert map_workspace.status_code == 200
    map_block = map_workspace.json()["sections"][1]["content_blocks"][0]
    assert map_block["kind"] == "figure"
    assert map_block["answer_numbers"] == [17, 18, 19, 20]


def test_react_ielts_answer_and_submit_contracts_remain_compatible() -> None:
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
        app.include_router(router)
        app.dependency_overrides[get_frontend_services] = lambda: services

        with TestClient(app) as client:
            missing = client.post("/api/v1/ielts/g20-test-1-listening/submit")

    assert missing.status_code == 422
    assert missing.json()["detail"]["missing_questions"] == list(range(1, 41))
