from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes.practice import router as practice_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.insights import router as insights_router
from app.api.routes.listening import router as listening_router
from app.api.routes.review import router as review_router
from app.api.routes.notebook import router as notebook_router
from app.api.routes.resources import router as resources_router
from app.api.routes.today import router as today_router
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
app.include_router(dashboard_router)
app.include_router(today_router)
app.include_router(insights_router)
app.include_router(listening_router)
app.include_router(review_router)
app.include_router(notebook_router)
app.include_router(resources_router)
