from functools import lru_cache

from app.clients.es_client import ElasticsearchClient
from app.core.config import get_settings
from app.services.account_service import AccountService
from app.services.cash_flow_service import CashFlowService
from app.services.chart_service import ChartService
from app.services.dividend_service import DividendService
from app.services.position_service import PositionService
from app.services.trade_service import TradeService


@lru_cache
def get_es_client() -> ElasticsearchClient:
    return ElasticsearchClient(get_settings())


def get_account_service() -> AccountService:
    return AccountService(get_es_client(), get_settings())


def get_chart_service() -> ChartService:
    return ChartService(get_es_client(), get_settings())


def get_position_service() -> PositionService:
    return PositionService(get_es_client(), get_settings())


def get_trade_service() -> TradeService:
    return TradeService(get_es_client(), get_settings())


def get_cash_flow_service() -> CashFlowService:
    return CashFlowService(get_es_client(), get_settings())


def get_dividend_service() -> DividendService:
    return DividendService(get_es_client(), get_settings())
