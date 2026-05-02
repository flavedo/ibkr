from fastapi import APIRouter, HTTPException, status

from app.schemas.market_sentiment import MarketSentimentResponse
from app.services.market_sentiment_service import MarketSentimentService

router = APIRouter(prefix="/market-sentiment", tags=["market-sentiment"])


@router.get("/", response_model=MarketSentimentResponse)
def get_market_sentiment() -> MarketSentimentResponse:
    try:
        service = MarketSentimentService()
        return service.get_sentiment()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch market sentiment: {exc}",
        ) from exc
