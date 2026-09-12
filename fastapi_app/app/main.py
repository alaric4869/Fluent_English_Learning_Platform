from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes.practice import router as practice_router
from app.config import FASTAPI_ROOT, settings
from app.database import SessionFactory
from app.database_migrations import upgrade_database
from app.seed import import_seed_data


@asynccontextmanager
async def lifespan(_: FastAPI):
    (FASTAPI_ROOT / "data").mkdir(parents=True, exist_ok=True)
    upgrade_database()
    with SessionFactory() as session:
        import_seed_data(session, settings.seed_path)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=FASTAPI_ROOT / "app" / "static"), name="static")
app.include_router(practice_router)
