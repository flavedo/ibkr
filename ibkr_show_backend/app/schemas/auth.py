from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthSessionResponse(BaseModel):
    authenticated: bool
    username: str | None = None
