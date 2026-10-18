from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes.practice import router as practice_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.insights import router as insights_router
from app.api.routes.listening import router as listening_router
from app.api.routes.review import router as review_router
from app.api.routes.notebook import router as notebook_router
from app.api.routes.resources import router as resources_router
from app.api.routes.speaking import router as speaking_router
from app.api.routes.today import router as today_router
from app.api.routes.writing import router as writing_router
from app.api.routes.frontend import router as frontend_router
from app.api.routes.frontend_insights import router as frontend_insights_router
from app.api.routes.frontend_notebook import router as frontend_notebook_router
from app.api.routes.frontend_resources import router as frontend_resources_router
from app.api.routes.frontend_review import router as frontend_review_router
from app.api.routes.frontend_ielts import router as frontend_ielts_router
from app.api.routes.frontend_practice import router as frontend_practice_router
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.frontend_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=FASTAPI_ROOT / "app" / "static"), name="static")
app.include_router(frontend_router)
app.include_router(frontend_resources_router)
app.include_router(frontend_review_router)
app.include_router(frontend_notebook_router)
app.include_router(frontend_insights_router)
app.include_router(frontend_ielts_router)
app.include_router(frontend_practice_router)
app.include_router(practice_router)
app.include_router(dashboard_router)
app.include_router(today_router)
app.include_router(insights_router)
app.include_router(listening_router)
app.include_router(review_router)
app.include_router(notebook_router)
app.include_router(resources_router)
app.include_router(speaking_router)
app.include_router(writing_router)
