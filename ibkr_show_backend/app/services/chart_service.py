from datetime import date

from app.clients.es_client import ElasticsearchClient
from app.core.config import Settings
from app.schemas.charts import EquityCurvePoint, EquityCurveResponse
from app.utils.dates import parse_date
from app.utils.es_query_builder import build_date_range_filter

INFERRED_DAILY_PNL_EPSILON = 0.01


class ChartService:
    def __init__(self, es_client: ElasticsearchClient, settings: Settings) -> None:
        self.es_client = es_client
        self.settings = settings

    def get_equity_curve(self, start_date: str | None, end_date: str | None) -> EquityCurveResponse:
        latest_report_date = self._get_latest_report_date()
        if latest_report_date is None:
            return EquityCurveResponse(items=[])

        effective_end = parse_date(end_date) or latest_report_date
        effective_start = parse_date(start_date)

        filters = [
            build_date_range_filter(
                "report_date",
                effective_start.isoformat() if effective_start else None,
                effective_end.isoformat(),
            )
        ]
        snapshots_response = self.es_client.search(
            index=self.settings.es_account_index,
            body={
                "query": {"bool": {"filter": [item for item in filters if item]}},
                "sort": [{"report_date": {"order": "asc"}}],
                "size": 2000,
                "_source": ["account_id", "report_date", "total_equity", "cnav_mtm", "cnav_twr"],
            },
        )
        snapshot_sources = [hit["_source"] for hit in snapshots_response.get("hits", {}).get("hits", [])]
        if not snapshot_sources:
            return EquityCurveResponse(items=[])

        account_id = snapshot_sources[-1].get("account_id")
        cash_flow_response = self._get_cash_flow_response(account_id, effective_end) if account_id else None
        cash_flow_curve = self._build_net_cost_curve(cash_flow_response)
        daily_net_flows = self._build_daily_net_flows(cash_flow_response)
        realized_pnl_curve = self._build_realized_pnl_curve(account_id, effective_end)

        items = []
        current_net_cost = 0.0
        current_realized_pnl = 0.0
        cash_flow_index = 0
        realized_pnl_index = 0
        previous_total_equity: float | None = None
        for source in snapshot_sources:
            report_date = source["report_date"]
            total_equity = source.get("total_equity")

            while cash_flow_index < len(cash_flow_curve) and cash_flow_curve[cash_flow_index][0] <= report_date:
                current_net_cost = cash_flow_curve[cash_flow_index][1]
                cash_flow_index += 1
            while realized_pnl_index < len(realized_pnl_curve) and realized_pnl_curve[realized_pnl_index][0] <= report_date:
                current_realized_pnl = realized_pnl_curve[realized_pnl_index][1]
                realized_pnl_index += 1

            net_cost = current_net_cost
            total_pnl = None
            if total_equity is not None and net_cost is not None:
                total_pnl = float(total_equity) - float(net_cost)

            daily_mtm = None
            if total_equity is not None and previous_total_equity is not None:
                daily_mtm = float(total_equity) - float(previous_total_equity) - daily_net_flows.get(report_date, 0.0)
                if abs(float(daily_mtm)) < INFERRED_DAILY_PNL_EPSILON:
                    daily_mtm = 0.0

            daily_twr = None
            if daily_mtm is not None and previous_total_equity not in (None, 0, 0.0):
                daily_twr = float(daily_mtm) / abs(float(previous_total_equity)) * 100.0

            items.append(
                EquityCurvePoint(
                    report_date=report_date,
                    total_equity=total_equity,
                    total_pnl=total_pnl,
                    net_cost=net_cost,
                    realized_pnl=current_realized_pnl,
                    daily_mtm=daily_mtm,
                    daily_twr=daily_twr,
                    cnav_twr=source.get("cnav_twr"),
                )
            )
            previous_total_equity = float(total_equity) if total_equity is not None else previous_total_equity
        return EquityCurveResponse(items=items)

    def _get_latest_report_date(self):
        response = self.es_client.search(
            index=self.settings.es_account_index,
            body={"size": 1, "sort": [{"report_date": {"order": "desc"}}], "_source": ["report_date"]},
        )
        hits = response.get("hits", {}).get("hits", [])
        if not hits:
            return None
        return parse_date(hits[0]["_source"]["report_date"])

    def _build_net_cost_curve(self, cash_flow_response: dict | None) -> list[tuple[str, float]]:
        if not cash_flow_response:
            return []

        cumulative = 0.0
        net_cost_points: list[tuple[str, float]] = []
        for hit in cash_flow_response.get("hits", {}).get("hits", []):
            source = hit["_source"]
            effective_date = source.get("settle_date") or source.get("report_date")
            if not effective_date:
                date_time = source.get("date_time")
                if date_time:
                    effective_date = str(date_time).split("T", 1)[0]
            if not effective_date:
                continue
            cumulative += float(source.get("amount_in_base") or 0.0)
            if net_cost_points and net_cost_points[-1][0] == effective_date:
                net_cost_points[-1] = (effective_date, cumulative)
            else:
                net_cost_points.append((effective_date, cumulative))

        return net_cost_points

    def _build_daily_net_flows(self, cash_flow_response: dict | None) -> dict[str, float]:
        if not cash_flow_response:
            return {}
        net_flows_by_date: dict[str, float] = {}
        for hit in cash_flow_response.get("hits", {}).get("hits", []):
            source = hit["_source"]
            effective_date = source.get("settle_date") or source.get("report_date")
            if not effective_date:
                date_time = source.get("date_time")
                if date_time:
                    effective_date = str(date_time).split("T", 1)[0]
            if not effective_date:
                continue
            net_flows_by_date[effective_date] = net_flows_by_date.get(effective_date, 0.0) + float(
                source.get("amount_in_base") or 0.0
            )

        return net_flows_by_date

    def _get_cash_flow_response(self, account_id: str, effective_end: date) -> dict:
        return self.es_client.search(
            index=self.settings.es_cash_flow_index,
            body={
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"account_id.keyword": account_id}},
                            {"term": {"flow_type.keyword": "Deposits/Withdrawals"}},
                            {"range": {"date_time": {"lte": effective_end.isoformat()}}},
                        ]
                    }
                },
                "sort": [{"date_time": {"order": "asc"}}],
                "size": 10000,
                "_source": ["date_time", "settle_date", "report_date", "amount_in_base"],
            },
        )

    def _build_realized_pnl_curve(self, account_id: str | None, effective_end: date) -> list[tuple[str, float]]:
        if not account_id:
            return []

        response = self.es_client.search(
            index=self.settings.es_trade_index,
            body={
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"account_id.keyword": account_id}},
                            {"range": {"trade_date": {"lte": effective_end.isoformat()}}},
                        ]
                    }
                },
                "sort": [
                    {"trade_date": {"order": "asc"}},
                    {"date_time": {"order": "asc", "missing": "_last"}},
                ],
                "size": 10000,
                "_source": ["trade_date", "fifo_pnl_realized"],
            },
        )

        cumulative = 0.0
        realized_points: list[tuple[str, float]] = []
        for hit in response.get("hits", {}).get("hits", []):
            source = hit["_source"]
            trade_date = source.get("trade_date")
            if not trade_date:
                continue
            cumulative += float(source.get("fifo_pnl_realized") or 0.0)
            if realized_points and realized_points[-1][0] == trade_date:
                realized_points[-1] = (trade_date, cumulative)
            else:
                realized_points.append((trade_date, cumulative))

        return realized_points
