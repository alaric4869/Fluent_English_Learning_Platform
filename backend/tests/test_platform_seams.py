from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.api.learner_context import LearnerContext, get_learner_context
from app.database import create_database_engine


def test_local_learner_context_can_be_replaced_by_an_auth_adapter() -> None:
    app = FastAPI()

    @app.get("/whoami")
    def whoami(context: LearnerContext = Depends(get_learner_context)):
        return {"user_key": context.user_key}

    app.dependency_overrides[get_learner_context] = lambda: LearnerContext("authenticated-user")

    with TestClient(app) as client:
        response = client.get("/whoami")

    assert response.json() == {"user_key": "authenticated-user"}


def test_sqlite_engine_factory_keeps_local_thread_compatibility() -> None:
    engine = create_database_engine("sqlite://")

    assert engine.dialect.name == "sqlite"
    with engine.connect() as connection:
        assert connection.exec_driver_sql("select 1").scalar_one() == 1
    engine.dispose()
