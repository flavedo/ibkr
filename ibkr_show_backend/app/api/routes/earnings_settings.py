from fastapi import APIRouter, HTTPException, status

from app.schemas.earnings_settings import (
    EarningsPushSettings,
    TestSendRequest,
    TestSendResponse,
)
from app.services.earnings_settings_service import (
    load_settings,
    save_settings,
    test_send,
    trigger_daily_push,
)

router = APIRouter(prefix="/earnings-settings", tags=["earnings-settings"])


@router.get("/push", response_model=EarningsPushSettings)
def get_push_settings() -> EarningsPushSettings:
    try:
        return load_settings()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.put("/push", response_model=EarningsPushSettings)
def update_push_settings(settings: EarningsPushSettings) -> EarningsPushSettings:
    try:
        return save_settings(settings)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post("/push/test-send", response_model=TestSendResponse)
def send_test_email(req: TestSendRequest) -> TestSendResponse:
    try:
        return test_send(
            smtp_server=req.smtp_server,
            smtp_port=req.smtp_port,
            smtp_username=req.smtp_username,
            smtp_password=req.smtp_password,
            sender_email=req.sender_email,
            target_email=req.target_email,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post("/push/trigger", response_model=TestSendResponse)
def trigger_push() -> TestSendResponse:
    try:
        return trigger_daily_push()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
