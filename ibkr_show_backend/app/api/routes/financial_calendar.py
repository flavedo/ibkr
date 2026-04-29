from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.financial_calendar import EarningsCalendarResponse, EconomicCalendarResponse
from app.services.financial_calendar_service import FinancialCalendarService

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


@router.get("/economic-events", response_model=EconomicCalendarResponse)
def get_economic_events(
    start_date: str = Query(),
    end_date: str = Query(),
) -> EconomicCalendarResponse:
    try:
        service = FinancialCalendarService()
        return service.get_economic_events(start_date, end_date)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Failed to fetch economic events: {exc}") from exc
