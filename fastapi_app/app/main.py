from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import models  # noqa: F401
from app.api.routes.practice import router as practice_router
from app.config import FASTAPI_ROOT, settings
from app.database import Base, SessionFactory, engine
from app.seed import import_seed_data


@asynccontextmanager
async def lifespan(_: FastAPI):
    (FASTAPI_ROOT / "data").mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)
    with SessionFactory() as session:
        import_seed_data(session, settings.seed_path)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=FASTAPI_ROOT / "app" / "static"), name="static")
app.include_router(practice_router)

