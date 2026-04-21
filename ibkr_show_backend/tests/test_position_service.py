from dataclasses import dataclass

from app.services.position_service import PositionService


@dataclass
class DummySettings:
    es_position_index: str = "position-index"
    es_trade_index: str = "trade-index"
    es_price_history_index: str = "price-index"


class StubESClient:
    def __init__(self, responses: list[dict]) -> None:
        self._responses = list(responses)
        self.calls: list[dict] = []

    def search(self, index: str, body: dict) -> dict:
        self.calls.append({"index": index, "body": body})
        return self._responses.pop(0)


def test_list_positions_returns_new_detail_fields_and_supports_new_sort_key() -> None:
    es_client = StubESClient(
        responses=[
            {"hits": {"hits": [{"_source": {"report_date": "2026-04-17"}}]}},
            {
                "hits": {
                    "total": {"value": 1},
                    "hits": [
                        {
                            "_source": {
                                "account_id": "U1",
                                "report_date": "2026-04-17",
                                "symbol": "AAPL",
                                "asset_class": "STK",
                                "average_cost_price": 175.0,
                                "cost_basis_money": 17500.0,
                                "total_realized_pnl": 120.5,
                                "realized_pnl_percent": 0.69,
                                "total_unrealized_pnl": 80.25,
                                "unrealized_pnl_percent": 0.46,
                                "previous_day_change_percent": 2.7,
                            }
                        }
                    ],
                }
            },
            {
                "aggregations": {
                    "by_position": {
                        "buckets": [
                            {
                                "key": {
                                    "account_id": "U1",
                                    "asset_class": "STK",
                                    "symbol": "AAPL",
                                },
                                "total_realized_pnl": {"value": 456.78},
                            }
                        ]
                    }
                }
            },
        ]
    )

    service = PositionService(es_client, DummySettings())
    response = service.list_positions(
        report_date=None,
        symbol=None,
        asset_class=None,
        sort_by="previous_day_change_percent",
        sort_order="desc",
        page=1,
        page_size=20,
    )

    assert response.items[0].symbol == "AAPL"
    assert response.items[0].average_cost_price == 175.0
    assert response.items[0].total_realized_pnl == 456.78
    assert response.items[0].realized_pnl_percent == 456.78 / 17500 * 100
    assert response.items[0].unrealized_pnl_percent == 0.46
    assert response.items[0].previous_day_change_percent == 2.7

    positions_call = es_client.calls[1]
    assert positions_call["index"] == "position-index"
    assert positions_call["body"]["sort"] == [{"previous_day_change_percent": {"order": "desc", "missing": "_last"}}]
    realized_pnl_call = es_client.calls[2]
    assert realized_pnl_call["index"] == "trade-index"
    assert realized_pnl_call["body"]["query"]["bool"]["filter"] == [
        {"range": {"trade_date": {"lte": "2026-04-17"}}},
        {"terms": {"account_id": ["U1"]}},
        {"terms": {"asset_class": ["STK"]}},
        {"terms": {"symbol": ["AAPL"]}},
    ]


def test_get_position_detail_returns_synthetic_bars_and_trade_markers() -> None:
    es_client = StubESClient(
        responses=[
            {
                "hits": {
                    "hits": [
                        {
                            "_source": {
                                "symbol": "AMD",
                                "description": "ADVANCED MICRO DEVICES",
                                "asset_class": "STK",
                                "report_date": "2026-04-16",
                                "open_price": 149.0,
                                "high_price": 155.0,
                                "low_price": 149.0,
                                "close_price": 155.0,
                            }
                        },
                        {
                            "_source": {
                                "symbol": "AMD",
                                "description": "ADVANCED MICRO DEVICES",
                                "asset_class": "STK",
                                "report_date": "2026-04-16",
                                "open_price": 150.0,
                                "high_price": 156.0,
                                "low_price": 151.0,
                                "close_price": 151.0,
                            }
                        },
                    ]
                }
            },
            {"hits": {"hits": []}},
            {
                "hits": {
                    "hits": [
                        {
                            "_source": {
                                "symbol": "AMD",
                                "description": "ADVANCED MICRO DEVICES",
                                "asset_class": "STK",
                                "trade_date": "2026-04-17",
                                "date_time": "2026-04-17T20:00:00Z",
                                "buy_sell": "BUY",
                                "quantity": 6.0,
                                "trade_price": 156.0,
                                "fifo_pnl_realized": 0.0,
                            }
                        }
                    ]
                }
            },
        ]
    )

    service = PositionService(es_client, DummySettings())
    response = service.get_position_detail(symbol="AMD", asset_class="STK")

    assert response.symbol == "AMD"
    assert len(response.bars) == 2
    assert response.bars[1].high_price == 156.0
    assert response.bars[1].low_price == 151.0
    assert response.trades[0].buy_sell == "BUY"
    assert es_client.calls[0]["index"] == "price-index"
    assert es_client.calls[1]["index"] == "position-index"
    assert es_client.calls[2]["index"] == "trade-index"


def test_get_positions_summary_uses_trade_aggregated_realized_pnl() -> None:
    es_client = StubESClient(
        responses=[
            {"hits": {"hits": [{"_source": {"report_date": "2026-04-17"}}]}},
            {
                "hits": {
                    "hits": [
                        {
                            "_source": {
                                "account_id": "U1",
                                "report_date": "2026-04-17",
                                "symbol": "AAPL",
                                "description": "Apple",
                                "asset_class": "STK",
                                "position_value": 1200.0,
                                "percent_of_nav": 12.0,
                                "cost_basis_money": 1000.0,
                                "total_realized_pnl": 0.0,
                                "total_unrealized_pnl": 80.0,
                                "total_fifo_pnl": 80.0,
                            }
                        },
                        {
                            "_source": {
                                "account_id": "U1",
                                "report_date": "2026-04-17",
                                "symbol": "MSFT",
                                "description": "Microsoft",
                                "asset_class": "STK",
                                "position_value": 900.0,
                                "percent_of_nav": 9.0,
                                "cost_basis_money": 700.0,
                                "total_realized_pnl": 0.0,
                                "total_unrealized_pnl": 40.0,
                                "total_fifo_pnl": 40.0,
                            }
                        },
                    ]
                }
            },
            {
                "aggregations": {
                    "by_position": {
                        "buckets": [
                            {
                                "key": {
                                    "account_id": "U1",
                                    "asset_class": "STK",
                                    "symbol": "AAPL",
                                },
                                "total_realized_pnl": {"value": 300.0},
                            },
                            {
                                "key": {
                                    "account_id": "U1",
                                    "asset_class": "STK",
                                    "symbol": "MSFT",
                                },
                                "total_realized_pnl": {"value": -20.0},
                            },
                        ]
                    }
                }
            },
        ]
    )

    service = PositionService(es_client, DummySettings())
    response = service.get_positions_summary(report_date=None, symbol=None, asset_class=None)

    assert response.total_realized_pnl == 280.0
    assert response.total_unrealized_pnl == 120.0
