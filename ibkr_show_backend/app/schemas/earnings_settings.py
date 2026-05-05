from pydantic import BaseModel


class EarningsPushSettings(BaseModel):
    enabled: bool = False
    push_time: str = "09:00"
    smtp_server: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    sender_email: str = ""
    target_email: str = ""


class TestSendRequest(BaseModel):
    smtp_server: str
    smtp_port: int = 587
    smtp_username: str
    smtp_password: str
    sender_email: str
    target_email: str


class TestSendResponse(BaseModel):
    success: bool
    message: str
