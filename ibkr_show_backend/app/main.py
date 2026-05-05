from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.api.routes import api_router, health_router
from app.core.auth import verify_token
from app.core.config import get_settings
from app.core.cors import configure_cors
from app.core.earnings_scheduler import start_scheduler, stop_scheduler
from app.core.logger import configure_logging

settings = get_settings()

configure_logging()


EXEMPT_PATHS = {"/api/auth/login", "/health"}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path not in EXEMPT_PATHS and path.startswith("/api"):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "未提供认证信息"},
                )
            token = auth_header.removeprefix("Bearer ")
            payload = verify_token(token)
            if payload is None:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "无效或已过期的认证信息，请重新登录"},
                )
        return await call_next(request)


@asynccontextmanager
async def lifespan(application: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
configure_cors(app)
app.add_middleware(AuthMiddleware)
app.include_router(health_router)
app.include_router(api_router)
