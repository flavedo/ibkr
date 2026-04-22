from dataclasses import dataclass

import pytest

from app.services.chart_service import ChartService


@dataclass
class DummySettings:
    es_account_index: str = "account-index"
    es_cash_flow_index: str = "cash-flow-index"
    es_trade_index: str = "trade-index"
    es_position_index: str = "position-index"


class StubESClient:
    def __init__(self, responses: list[dict]) -> None:
        self._responses = list(responses)

    def search(self, index: str, body: dict) -> dict:
        return self._responses.pop(0)


def test_get_equity_curve_builds_equity_pnl_and_net_cost_series() -> None:
    es_client = StubESClient(
        responses=[
            {"hits": {"hits": [{"_source": {"report_date": "2026-04-17"}}]}},
            {
                "hits": {
                    "hits": [
                        {"_source": {"account_id": "U1", "report_date": "2026-04-15", "total_equity": 100.0}},
                        {"_source": {"account_id": "U1", "report_date": "2026-04-16", "total_equity": 130.000001}},
                        {"_source": {"account_id": "U1", "report_date": "2026-04-17", "total_equity": 150.0, "cnav_mtm": -2.0, "cnav_twr": -1.2}},
                    ]
                }
            },
            {
                "hits": {
                    "hits": [
                        {
                            "_source": {
                                "date_time": "2026-04-15T00:00:00",
                                "settle_date": "2026-04-15",
                                "report_date": "2026-04-15",
                                "amount_in_base": 80.0,
                            }
                        },
                        {
                            "_source": {
                                "date_time": "2026-04-16T00:00:00",
                                "settle_date": "2026-04-16",
                                "report_date": "2026-04-16",
                                "amount_in_base": 20.0,
                            }
                        },
                        {
                            "_source": {
                                "date_time": "2026-04-17T00:00:00",
                                "settle_date": "2026-04-17",
                                "report_date": "2026-04-17",
                                "amount_in_base": 10.0,
                            }
                        },
                    ]
                }
            },
            {
                "hits": {
                    "hits": [
                        {
                            "_source": {
                                "trade_date": "2026-04-15",
                                "fifo_pnl_realized": 12.0,
                            }
                        },
                        {
                            "_source": {
                                "trade_date": "2026-04-17",
                                "fifo_pnl_realized": 8.0,
                            }
                        },
                    ]
                }
            },
        ]
    )

    service = ChartService(es_client, DummySettings())
    response = service.get_equity_curve(None, None)

    assert [item.report_date for item in response.items] == ["2026-04-15", "2026-04-16", "2026-04-17"]
    assert [item.net_cost for item in response.items] == [80.0, 100.0, 110.0]
    assert [item.total_pnl for item in response.items] == pytest.approx([20.0, 30.0, 40.0])
    assert [item.realized_pnl for item in response.items] == [12.0, 12.0, 20.0]
    assert response.items[0].daily_mtm is None
    assert response.items[1].daily_mtm == pytest.approx(10.000001)
    assert response.items[2].daily_mtm == pytest.approx(-2.0)
    assert response.items[0].daily_twr is None
    assert response.items[1].daily_twr == pytest.approx(10.000001)
    assert response.items[2].daily_twr == pytest.approx(-1.2)


def test_get_equity_curve_drops_near_zero_inferred_daily_pnl() -> None:
    es_client = StubESClient(
        responses=[
            {"hits": {"hits": [{"_source": {"report_date": "2026-04-03"}}]}},
            {
                "hits": {
                    "hits": [
                        {"_source": {"account_id": "U1", "report_date": "2026-04-02", "total_equity": 59062.647184219}},
                        {"_source": {"account_id": "U1", "report_date": "2026-04-03", "total_equity": 59062.647186383}},
                    ]
                }
            },
            {"hits": {"hits": []}},
            {"hits": {"hits": []}},
        ]
    )

    service = ChartService(es_client, DummySettings())
    response = service.get_equity_curve("2026-04-02", "2026-04-03")

    assert [item.daily_mtm for item in response.items] == [None, None]
    assert [item.daily_twr for item in response.items] == [None, None]


def test_get_equity_curve_aligns_net_cost_to_settle_date() -> None:
    es_client = StubESClient(
        responses=[
            {"hits": {"hits": [{"_source": {"report_date": "2026-01-02"}}]}},
            {
                "hits": {
                    "hits": [
                        {"_source": {"account_id": "U1", "report_date": "2025-12-29", "total_equity": 43114.89}},
                        {"_source": {"account_id": "U1", "report_date": "2025-12-30", "total_equity": 51878.12}},
                    ]
                }
            },
            {
                "hits": {
                    "hits": [
                        {
                            "_source": {
                                "date_time": "2025-12-29T21:35:54",
                                "settle_date": "2025-12-30",
                                "report_date": "2025-12-30",
                                "amount_in_base": 8581.2,
                            }
                        }
                    ]
                }
            },
            {"hits": {"hits": []}},
        ]
    )

    service = ChartService(es_client, DummySettings())
    response = service.get_equity_curve("2025-12-29", "2026-01-02")

    assert [item.report_date for item in response.items] == ["2025-12-29", "2025-12-30"]
    assert [item.net_cost for item in response.items] == [0.0, 8581.2]
    assert [round(item.total_pnl or 0.0, 2) for item in response.items] == [43114.89, 43296.92]
