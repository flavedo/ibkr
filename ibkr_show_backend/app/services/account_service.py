from app.clients.es_client import ElasticsearchClient
from app.core.config import Settings
from app.schemas.account import AccountDeltaMetric, AccountOverviewResponse, LatestReportDateResponse


class AccountService:
    def __init__(self, es_client: ElasticsearchClient, settings: Settings) -> None:
        self.es_client = es_client
        self.settings = settings

    def get_latest_report_date(self) -> LatestReportDateResponse | None:
        response = self.es_client.search(
            index=self.settings.es_account_index,
            body={
                "size": 1,
                "sort": [{"report_date": {"order": "desc"}}],
                "_source": ["report_date"],
            },
        )
        hits = response.get("hits", {}).get("hits", [])
        if not hits:
            return None
        source = hits[0]["_source"]
        return LatestReportDateResponse(report_date=source["report_date"])

    def get_overview(self) -> AccountOverviewResponse | None:
        response = self.es_client.search(
            index=self.settings.es_account_index,
            body={
                "size": 2,
                "sort": [{"report_date": {"order": "desc"}}],
                "_source": [
                    "account_id",
                    "report_date",
                    "currency",
                    "total_equity",
                    "cash",
                    "stock_value",
                    "options_value",
                    "funds_value",
                    "crypto_value",
                    "interest_accruals",
                    "dividend_accruals",
                    "margin_financing_charge_accruals",
                    "fifo_total_realized_pnl",
                    "fifo_total_unrealized_pnl",
                    "fifo_total_pnl",
                    "cnav_twr",
                    "crtt_dividends_ytd",
                    "crtt_broker_interest_ytd",
                    "crtt_commissions_ytd",
                ],
            },
        )
        hits = response.get("hits", {}).get("hits", [])
        if not hits:
            return None
        overview_source = dict(hits[0]["_source"])
        account_id = overview_source["account_id"]
        report_date = overview_source["report_date"]

        total_realized_pnl = self._get_total_realized_pnl(account_id, report_date)
        total_unrealized_pnl = self._get_total_unrealized_pnl(account_id, report_date)

        overview_source["fifo_total_realized_pnl"] = total_realized_pnl
        overview_source["fifo_total_unrealized_pnl"] = total_unrealized_pnl
        overview_source["fifo_total_pnl"] = total_realized_pnl + total_unrealized_pnl
        overview_source["ytd_twr"] = self._get_ytd_twr(account_id, report_date)

        overview_source["crtt_dividends_ytd"] = self._get_ytd_dividends(account_id, report_date)

        previous_source = dict(hits[1]["_source"]) if len(hits) > 1 else None
        if previous_source is not None:
            previous_report_date = previous_source["report_date"]
            previous_total_realized_pnl = self._get_total_realized_pnl(account_id, previous_report_date)
            previous_total_unrealized_pnl = self._get_total_unrealized_pnl(account_id, previous_report_date)
            previous_total_pnl = previous_total_realized_pnl + previous_total_unrealized_pnl

            overview_source["total_equity_delta"] = self._build_delta_metric(
                overview_source.get("total_equity"),
                previous_source.get("total_equity"),
            )
            overview_source["fifo_total_realized_pnl_delta"] = self._build_delta_metric(
                total_realized_pnl,
                previous_total_realized_pnl,
            )
            overview_source["fifo_total_unrealized_pnl_delta"] = self._build_delta_metric(
                total_unrealized_pnl,
                previous_total_unrealized_pnl,
            )
            overview_source["fifo_total_pnl_delta"] = self._build_delta_metric(
                overview_source["fifo_total_pnl"],
                previous_total_pnl,
            )

        return AccountOverviewResponse(**overview_source)

    def _get_ytd_twr(self, account_id: str, report_date: str) -> float | None:
        report_year = report_date[:4]
        response = self.es_client.search(
            index=self.settings.es_account_index,
            body={
                "size": 2000,
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"account_id": account_id}},
                            {"range": {"report_date": {"gte": f"{report_year}-01-01", "lte": report_date}}},
                        ]
                    }
                },
                "sort": [{"report_date": {"order": "asc"}}],
                "_source": ["report_date", "cnav_twr"],
            },
        )

        twr_values = [
            float(hit["_source"]["cnav_twr"])
            for hit in response.get("hits", {}).get("hits", [])
            if hit.get("_source", {}).get("cnav_twr") is not None
        ]
        if not twr_values:
            return None

        cumulative_return = 1.0
        for daily_twr in twr_values:
            cumulative_return *= 1.0 + daily_twr / 100.0

        return (cumulative_return - 1.0) * 100.0

    def _get_ytd_dividends(self, account_id: str, report_date: str) -> float | None:
        report_year = report_date[:4]
        response = self.es_client.search(
            index=self.settings.es_cash_flow_index,
            body={
                "size": 0,
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"account_id": account_id}},
                            {"term": {"flow_type": "Dividend"}},
                            {"range": {"date_time": {"gte": f"{report_year}-01-01", "lte": report_date}}},
                        ]
                    }
                },
                "aggs": {
                    "total": {"sum": {"field": "amount"}}
                }
            },
        )
        total = response.get("aggregations", {}).get("total", {}).get("value")
        return total if total is not None else None

    def _get_total_realized_pnl(self, account_id: str, report_date: str) -> float:
        response = self.es_client.search(
            index=self.settings.es_trade_index,
            body={
                "size": 0,
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"account_id": account_id}},
                            {"range": {"trade_date": {"lte": report_date}}},
                        ]
                    }
                },
                "aggs": {
                    "total_realized_pnl": {
                        "sum": {"field": "fifo_pnl_realized"}
                    }
                },
            },
        )
        return float(response.get("aggregations", {}).get("total_realized_pnl", {}).get("value") or 0.0)

    def _get_total_unrealized_pnl(self, account_id: str, report_date: str) -> float:
        response = self.es_client.search(
            index=self.settings.es_position_index,
            body={
                "size": 0,
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"account_id": account_id}},
                            {"term": {"report_date": report_date}},
                        ]
                    }
                },
                "aggs": {
                    "total_unrealized_pnl": {
                        "sum": {"field": "total_unrealized_pnl"}
                    }
                },
            },
        )
        return float(response.get("aggregations", {}).get("total_unrealized_pnl", {}).get("value") or 0.0)

    def _build_delta_metric(
        self,
        current_value: float | None,
        previous_value: float | None,
    ) -> AccountDeltaMetric | None:
        if current_value is None or previous_value is None:
            return None

        amount_change = float(current_value) - float(previous_value)
        percent_change = None
        if float(previous_value) != 0.0:
            percent_change = amount_change / abs(float(previous_value)) * 100.0

        return AccountDeltaMetric(
            amount_change=amount_change,
            percent_change=percent_change,
        )
