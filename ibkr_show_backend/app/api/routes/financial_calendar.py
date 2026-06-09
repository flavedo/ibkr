from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.financial_calendar import EarningsCalendarResponse, MacroEventResponse
from app.services.financial_calendar_service import FinancialCalendarService
from app.services.macro_event_service import MacroEventService

router = APIRouter(prefix="/financial-calendar", tags=["financial-calendar"])


@router.get("/earnings", response_model=EarningsCalendarResponse)
def get_earnings_calendar(
    start_date: str = Query(),
    end_date: str = Query(),
) -> EarningsCalendarResponse:
    try:
        service = FinancialCalendarService()
        return service.get_earnings(start_date, end_date)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Failed to fetch earnings calendar: {exc}") from exc


@router.get("/macro-events", response_model=MacroEventResponse)
def get_macro_events(
    start_date: str = Query(),
    end_date: str = Query(),
) -> MacroEventResponse:
    try:
        service = MacroEventService()
        return service.get_events(start_date, end_date)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Failed to fetch macro events: {exc}") from exc
