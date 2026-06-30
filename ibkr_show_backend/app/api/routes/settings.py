from fastapi import APIRouter, HTTPException, status

from app.schemas.settings import SystemSettings, TestSendRequest, TestSendResponse
from app.services.settings_service import load_settings, save_settings
from app.services.earnings_settings_service import test_send, trigger_daily_push

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SystemSettings)
def get_settings() -> SystemSettings:
    try:
        return load_settings()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.put("", response_model=SystemSettings)
def update_settings(settings: SystemSettings) -> SystemSettings:
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
