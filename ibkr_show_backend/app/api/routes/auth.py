from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.deps import get_optional_auth_session
from app.core.auth import SESSION_COOKIE_NAME, create_session_token
from app.core.config import Settings, get_settings
from app.schemas.auth import AuthSessionResponse, LoginRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/session", response_model=AuthSessionResponse)
def get_auth_session(
    auth_session=Depends(get_optional_auth_session),
) -> AuthSessionResponse:
    if auth_session is None:
        return AuthSessionResponse(authenticated=False)

    return AuthSessionResponse(authenticated=True, username=auth_session.username)


@router.post("/login", response_model=AuthSessionResponse)
def login(
    payload: LoginRequest,
    response: Response,
    settings: Settings = Depends(get_settings),
) -> AuthSessionResponse:
    if payload.username != settings.auth_username or payload.password != settings.auth_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    session_token = create_session_token(
        username=payload.username,
        secret=settings.auth_session_secret,
        max_age_seconds=settings.auth_session_max_age_seconds,
    )
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        max_age=settings.auth_session_max_age_seconds,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )
    return AuthSessionResponse(authenticated=True, username=payload.username)


@router.post("/logout", response_model=AuthSessionResponse)
def logout(response: Response) -> AuthSessionResponse:
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/", samesite="lax")
    return AuthSessionResponse(authenticated=False)
