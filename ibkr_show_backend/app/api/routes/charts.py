from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_chart_service
from app.clients.es_client import ESClientError
from app.schemas.charts import EquityCurveResponse
from app.services.chart_service import ChartService

router = APIRouter(prefix="/charts", tags=["charts"])


@router.get("/equity-curve", response_model=EquityCurveResponse)
def get_equity_curve(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    service: ChartService = Depends(get_chart_service),
) -> EquityCurveResponse:
    try:
        return service.get_equity_curve(start_date=start_date, end_date=end_date)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except ESClientError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
