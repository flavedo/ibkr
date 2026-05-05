from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import api_router, health_router
from app.core.config import get_settings
from app.core.cors import configure_cors
from app.core.earnings_scheduler import start_scheduler, stop_scheduler
from app.core.logger import configure_logging

settings = get_settings()

configure_logging()


@asynccontextmanager
async def lifespan(application: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
configure_cors(app)
app.include_router(health_router)
app.include_router(api_router)
