from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.routes.dashboard import get_services, router as dashboard_router
from app.api.routes.practice import router as practice_router
from app.composition import build_application_services
from app.config import FASTAPI_ROOT
from app.database import Base
from app.domain.learning_evidence.entities import Skill
from app.models.learning_evidence import LearningResource


def test_dashboard_weekly_review_and_home_redirect_render() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        _add_resources(session)
        services = build_application_services(session)
        app = FastAPI()
        app.mount(
            "/static",
            StaticFiles(directory=FASTAPI_ROOT / "app" / "static"),
            name="static",
        )
        app.include_router(practice_router)
        app.include_router(dashboard_router)
        app.dependency_overrides[get_services] = lambda: services

        with TestClient(app) as client:
            dashboard = client.get("/dashboard")
            weekly = client.get("/weekly-review")
            agent = client.post("/api/agent/weekly-coaching")
            home = client.get("/", follow_redirects=False)

        assert dashboard.status_code == 200
        assert "今天具体学什么" in dashboard.text
        assert "REVIEWS DUE TODAY" in dashboard.text
        assert "添加材料" in dashboard.text
        assert weekly.status_code == 200
        assert "这周的努力，留下了什么证据" in weekly.text
        assert "Good / Easy" in weekly.text
        assert "AI LEARNING COACH" in weekly.text
        assert "AI Agent 当前未启用" in weekly.text
        assert agent.status_code == 503
        assert home.status_code == 307
        assert home.headers["location"] == "/dashboard"


def _add_resources(session: Session) -> None:
    session.add_all(
        [
            LearningResource(
                slug=f"{skill.value}-dashboard-resource",
                title=f"{skill.value.title()} dashboard resource",
                resource_type="practice",
                skill=skill.value,
                topic="Daily English",
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
