from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.frontend_dependencies import get_frontend_services
from app.api.routes.frontend import router
from app.composition import build_application_services
from app.database import Base
from app.domain.learning_evidence.entities import Skill
from app.models.learning_evidence import LearningResource


def test_react_frontend_contract_exposes_dashboard_and_today() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        session.add_all(
            [
                LearningResource(
                    slug=f"{skill.value}-frontend-contract",
                    title=f"{skill.value.title()} practice",
                    resource_type="practice",
                    skill=skill.value,
                    topic="IELTS General Training",
                    difficulty="intermediate",
                    estimated_duration_minutes=30,
                    content={},
                    tags=[],
                    priority=50,
                    active=True,
                )
                for skill in Skill
            ]
        )
        session.commit()
        services = build_application_services(session)
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_frontend_services] = lambda: services

        with TestClient(app) as client:
            health = client.get("/api/v1/health")
            dashboard = client.get("/api/v1/dashboard")
            today = client.get("/api/v1/today")

    assert health.json() == {"status": "ok", "api_version": "v1"}
    assert dashboard.status_code == 200
    assert dashboard.json()["total_minutes"] == 110
    assert len(dashboard.json()["modules"]) == 4
    assert dashboard.json()["modules"][0]["resource_title"] == "Listening practice"
    assert today.status_code == 200
    assert len(today.json()["modules"]) == 4
    assert today.json()["modules"][0]["instruction"]
    assert today.json()["modules"][0]["session"]["status"] == "not_started"
