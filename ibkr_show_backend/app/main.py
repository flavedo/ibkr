from fastapi import FastAPI

from app.api.routes import api_router, health_router
from app.core.config import get_settings
from app.core.cors import configure_cors
from app.core.logger import configure_logging

settings = get_settings()

configure_logging()
app = FastAPI(title=settings.app_name)
configure_cors(app)
app.include_router(health_router)
app.include_router(api_router)
