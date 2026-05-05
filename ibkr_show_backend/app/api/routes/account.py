from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_account_service
from app.clients.es_client import ESClientError
from app.schemas.account import AccountOverviewResponse, ExchangeRateResponse, LatestReportDateResponse
from app.services.account_service import AccountService
from app.services.exchange_rate_service import get_exchange_rate

router = APIRouter(prefix="/account", tags=["account"])


@router.get("/overview", response_model=AccountOverviewResponse)
def get_account_overview(
    service: AccountService = Depends(get_account_service),
) -> AccountOverviewResponse:
    try:
        overview = service.get_overview()
    except ESClientError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    if overview is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No account overview data found.")
    return overview


@router.get("/latest-report-date", response_model=LatestReportDateResponse)
def get_latest_report_date(
    service: AccountService = Depends(get_account_service),
) -> LatestReportDateResponse:
    try:
        latest = service.get_latest_report_date()
    except ESClientError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    if latest is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No report date found.")
    return latest


@router.get("/exchange-rate", response_model=ExchangeRateResponse)
def get_exchange_rate(
    from_currency: str = Query(default="USD"),
    to_currency: str = Query(default="CNH"),
) -> ExchangeRateResponse:
    rate = get_exchange_rate(from_currency, to_currency)
    return ExchangeRateResponse(
        from_currency=from_currency,
        to_currency=to_currency,
        rate=rate,
    )
