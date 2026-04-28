from app.clients.es_client import ElasticsearchClient
from app.core.config import Settings
from app.schemas.positions import (
    PositionDetailBar,
    PositionDetailResponse,
    PositionDetailTradeMarker,
    PositionAssetDistributionItem,
    PositionConcentrationItem,
    PositionItem,
    PositionListResponse,
    PositionSummaryResponse,
)
from app.utils.es_query_builder import (
    build_date_range_filter,
    build_search_body,
    build_sort_clause,
    build_term_filter,
)
from app.utils.pagination import build_pagination_info

POSITION_SORT_FIELDS = {
    "position_value": "position_value",
    "percent_of_nav": "percent_of_nav",
    "total_unrealized_pnl": "total_unrealized_pnl",
    "total_realized_pnl": "total_realized_pnl",
    "average_cost_price": "average_cost_price",
    "previous_day_change_percent": "previous_day_change_percent",
    "symbol": "symbol",
    "quantity": "quantity",
}


class PositionService:
    def __init__(self, es_client: ElasticsearchClient, settings: Settings) -> None:
        self.es_client = es_client
        self.settings = settings

    def list_positions(
        self,
        report_date: str | None,
        symbol: str | None,
        asset_class: str | None,
        sort_by: str,
        sort_order: str,
        page: int,
        page_size: int,
    ) -> PositionListResponse:
        effective_report_date = report_date or self._get_latest_report_date()
        if effective_report_date is None:
            return PositionListResponse(items=[], pagination=build_pagination_info(page, page_size, 0))

        filters = [
            build_term_filter("report_date", effective_report_date),
            build_term_filter("symbol", symbol),
            build_term_filter("asset_class", asset_class),
        ]
        body = build_search_body(
            filters=[item for item in filters if item],
            sort=build_sort_clause(sort_by, sort_order, POSITION_SORT_FIELDS),
            page=page,
            page_size=page_size,
            source_fields=[
                "account_id",
                "report_date",
                "symbol",
                "description",
                "asset_class",
                "quantity",
                "mark_price",
                "position_value",
                "percent_of_nav",
                "average_cost_price",
                "cost_basis_money",
                "total_realized_pnl",
                "realized_pnl_percent",
                "total_unrealized_pnl",
                "unrealized_pnl_percent",
                "previous_day_change_percent",
            ],
        )
        response = self.es_client.search(index=self.settings.es_position_index, body=body)
        hits = response.get("hits", {})
        total = hits.get("total", {}).get("value", 0)
        documents = [dict(hit["_source"]) for hit in hits.get("hits", [])]
        self._apply_trade_realized_pnl(documents=documents, report_date=effective_report_date)
        items = [PositionItem(**document) for document in documents]
        return PositionListResponse(
            items=items,
            pagination=build_pagination_info(page, min(page_size, 200), total),
        )

    def get_positions_summary(
        self,
        report_date: str | None,
        symbol: str | None,
        asset_class: str | None,
    ) -> PositionSummaryResponse:
        effective_report_date = report_date or self._get_latest_report_date()
        if effective_report_date is None:
            return PositionSummaryResponse(top_positions=[], asset_distribution=[])

        filters = [
            build_term_filter("report_date", effective_report_date),
            build_term_filter("symbol", symbol),
            build_term_filter("asset_class", asset_class),
        ]
        body = build_search_body(
            filters=[item for item in filters if item],
            sort=[{"position_value": {"order": "desc", "missing": "_last"}}],
            page=1,
            page_size=200,
            source_fields=[
                "report_date",
                "symbol",
                "description",
                "asset_class",
                "position_value",
                "percent_of_nav",
                "cost_basis_money",
                "total_realized_pnl",
                "total_unrealized_pnl",
                "total_fifo_pnl",
            ],
        )
        response = self.es_client.search(index=self.settings.es_position_index, body=body)
        hits = response.get("hits", {}).get("hits", [])
        documents = [dict(hit["_source"]) for hit in hits]
        self._apply_trade_realized_pnl(documents=documents, report_date=effective_report_date)

        def sum_field(field: str) -> float:
            return sum(float(item.get(field) or 0.0) for item in documents)

        top_positions = [
            PositionConcentrationItem(
                symbol=item.get("symbol"),
                description=item.get("description"),
                asset_class=item.get("asset_class"),
                position_value=float(item.get("position_value") or 0.0),
                percent_of_nav=item.get("percent_of_nav"),
            )
            for item in documents[:5]
        ]

        distribution: dict[str, dict[str, float | int | None]] = {}
        for item in documents:
            asset_key = item.get("asset_class") or "UNKNOWN"
            bucket = distribution.setdefault(
                asset_key,
                {"asset_class": item.get("asset_class"), "position_value": 0.0, "positions_count": 0},
            )
            bucket["position_value"] = float(bucket["position_value"]) + float(item.get("position_value") or 0.0)
            bucket["positions_count"] = int(bucket["positions_count"]) + 1

        asset_distribution = [
            PositionAssetDistributionItem(
                asset_class=value["asset_class"],
                position_value=float(value["position_value"]),
                positions_count=int(value["positions_count"]),
            )
            for value in sorted(distribution.values(), key=lambda item: float(item["position_value"]), reverse=True)
        ]

        return PositionSummaryResponse(
            report_date=effective_report_date,
            total_positions=len(documents),
            total_position_value=sum_field("position_value"),
            total_cost_basis_money=sum_field("cost_basis_money"),
            total_realized_pnl=sum_field("total_realized_pnl"),
            total_unrealized_pnl=sum_field("total_unrealized_pnl"),
            total_fifo_pnl=sum_field("total_fifo_pnl"),
            top_positions=top_positions,
            asset_distribution=asset_distribution,
        )

    def get_position_detail(
        self,
        symbol: str,
        asset_class: str | None,
    ) -> PositionDetailResponse:
        filters = [
            build_term_filter("symbol", symbol),
            build_term_filter("asset_class", asset_class),
        ]
        price_body = build_search_body(
            filters=[item for item in filters if item],
            sort=[{"report_date": {"order": "asc", "missing": "_last"}}],
            page=1,
            page_size=1000,
            max_page_size=5000,
            source_fields=[
                "symbol",
                "description",
                "asset_class",
                "report_date",
                "open_price",
                "high_price",
                "low_price",
                "close_price",
            ],
        )
        position_body = build_search_body(
            filters=[item for item in filters if item],
            sort=[{"report_date": {"order": "asc", "missing": "_last"}}],
            page=1,
            page_size=1000,
            max_page_size=5000,
            source_fields=[
                "symbol",
                "description",
                "asset_class",
                "report_date",
                "open_price",
                "mark_price",
                "quantity",
            ],
        )
        trade_body = build_search_body(
            filters=[item for item in filters if item],
            sort=[
                {"trade_date": {"order": "asc", "missing": "_last"}},
                {"date_time": {"order": "asc", "missing": "_last"}},
            ],
            page=1,
            page_size=1000,
            max_page_size=5000,
            source_fields=[
                "symbol",
                "description",
                "asset_class",
                "trade_date",
                "date_time",
                "buy_sell",
                "quantity",
                "trade_price",
                "fifo_pnl_realized",
            ],
        )

        price_hits = self.es_client.search(index=self.settings.es_price_history_index, body=price_body).get("hits", {}).get("hits", [])
        position_hits = self.es_client.search(index=self.settings.es_position_index, body=position_body).get("hits", {}).get("hits", [])
        trade_hits = self.es_client.search(index=self.settings.es_trade_index, body=trade_body).get("hits", {}).get("hits", [])

        price_docs = [hit["_source"] for hit in price_hits]
        position_docs = [hit["_source"] for hit in position_hits]
        trade_docs = [hit["_source"] for hit in trade_hits]
        trade_prices_by_date: dict[str, list[float]] = {}
        for document in trade_docs:
            trade_date = document.get("trade_date")
            trade_price = document.get("trade_price")
            if trade_date and trade_price is not None:
                trade_prices_by_date.setdefault(str(trade_date), []).append(float(trade_price))

        bars = []
        if price_docs:
            for document in price_docs:
                report_date = document["report_date"]
                open_price = document.get("open_price")
                close_price = document.get("close_price")
                high_price = document.get("high_price")
                low_price = document.get("low_price")
                trade_price_points = trade_prices_by_date.get(str(report_date), [])
                if trade_price_points:
                    numeric_points = [
                        value
                        for value in [
                            float(open_price) if open_price is not None else None,
                            float(close_price) if close_price is not None else None,
                            float(high_price) if high_price is not None else None,
                            float(low_price) if low_price is not None else None,
                            *trade_price_points,
                        ]
                        if value is not None
                    ]
                    if numeric_points:
                        high_price = max(numeric_points)
                        low_price = min(numeric_points)

                bars.append(
                    PositionDetailBar(
                        report_date=report_date,
                        open_price=open_price,
                        high_price=high_price,
                        low_price=low_price,
                        close_price=close_price,
                        quantity=None,
                    )
                )
        else:
            for document in position_docs:
                open_price = document.get("open_price")
                close_price = document.get("mark_price")
                price_points = [
                    value
                    for value in [
                        float(open_price) if open_price is not None else None,
                        float(close_price) if close_price is not None else None,
                        *trade_prices_by_date.get(str(document.get("report_date")), []),
                    ]
                    if value is not None
                ]
                bars.append(
                    PositionDetailBar(
                        report_date=document["report_date"],
                        open_price=open_price,
                        high_price=max(price_points) if price_points else None,
                        low_price=min(price_points) if price_points else None,
                        close_price=close_price,
                        quantity=document.get("quantity"),
                    )
                )

        trades = [
            PositionDetailTradeMarker(
                trade_date=document.get("trade_date"),
                date_time=document.get("date_time"),
                buy_sell=document.get("buy_sell"),
                quantity=document.get("quantity"),
                trade_price=document.get("trade_price"),
                fifo_pnl_realized=document.get("fifo_pnl_realized"),
            )
            for document in trade_docs
        ]

        metadata = (
            price_docs[-1]
            if price_docs
            else (position_docs[-1] if position_docs else (trade_docs[-1] if trade_docs else {}))
        )

        return PositionDetailResponse(
            symbol=metadata.get("symbol"),
            description=metadata.get("description"),
            asset_class=metadata.get("asset_class"),
            bars=bars,
            trades=trades,
        )

    def _get_latest_report_date(self) -> str | None:
        response = self.es_client.search(
            index=self.settings.es_position_index,
            body={"size": 1, "sort": [{"report_date": {"order": "desc"}}], "_source": ["report_date"]},
        )
        hits = response.get("hits", {}).get("hits", [])
        if not hits:
            return None
        return hits[0]["_source"]["report_date"]

    def _apply_trade_realized_pnl(self, documents: list[dict], report_date: str) -> None:
        realized_lookup = self._fetch_trade_realized_pnl_lookup(documents=documents, report_date=report_date)
        for document in documents:
            realized_pnl = realized_lookup.get(
                (
                    str(document.get("account_id") or ""),
                    str(document.get("asset_class") or ""),
                    str(document.get("symbol") or ""),
                ),
                0.0,
            )
            document["total_realized_pnl"] = realized_pnl
            document["realized_pnl_percent"] = self._calculate_percentage(
                realized_pnl,
                document.get("cost_basis_money"),
            )
            unrealized_pnl = document.get("total_unrealized_pnl")
            if realized_pnl is not None and unrealized_pnl is not None:
                document["total_fifo_pnl"] = realized_pnl + float(unrealized_pnl)

    def _fetch_trade_realized_pnl_lookup(
        self,
        documents: list[dict],
        report_date: str,
    ) -> dict[tuple[str, str, str], float]:
        position_keys = {
            (
                str(item.get("account_id") or ""),
                str(item.get("asset_class") or ""),
                str(item.get("symbol") or ""),
            )
            for item in documents
            if item.get("account_id") and item.get("asset_class") and item.get("symbol")
        }
        if not position_keys:
            return {}

        filters: list[dict] = [build_date_range_filter("trade_date", None, report_date)]
        account_ids = sorted({key[0] for key in position_keys})
        asset_classes = sorted({key[1] for key in position_keys})
        symbols = sorted({key[2] for key in position_keys})
        if account_ids:
            filters.append({"terms": {"account_id": account_ids}})
        if asset_classes:
            filters.append({"terms": {"asset_class": asset_classes}})
        if symbols:
            filters.append({"terms": {"symbol": symbols}})

        lookup: dict[tuple[str, str, str], float] = {}
        after_key: dict | None = None

        while True:
            composite = {
                "size": 1000,
                "sources": [
                    {"account_id": {"terms": {"field": "account_id"}}},
                    {"asset_class": {"terms": {"field": "asset_class"}}},
                    {"symbol": {"terms": {"field": "symbol"}}},
                ],
            }
            if after_key is not None:
                composite["after"] = after_key

            response = self.es_client.search(
                index=self.settings.es_trade_index,
                body={
                    "size": 0,
                    "query": {"bool": {"filter": [item for item in filters if item]}},
                    "aggs": {
                        "by_position": {
                            "composite": composite,
                            "aggs": {
                                "total_realized_pnl": {
                                    "sum": {"field": "fifo_pnl_realized"}
                                }
                            },
                        }
                    },
                },
            )
            aggregation = response.get("aggregations", {}).get("by_position", {})
            for bucket in aggregation.get("buckets", []):
                key = bucket.get("key", {})
                position_key = (
                    str(key.get("account_id") or ""),
                    str(key.get("asset_class") or ""),
                    str(key.get("symbol") or ""),
                )
                if position_key in position_keys:
                    lookup[position_key] = float(
                        bucket.get("total_realized_pnl", {}).get("value") or 0.0
                    )

            after_key = aggregation.get("after_key")
            if after_key is None:
                break

        return lookup

    @staticmethod
    def _calculate_percentage(numerator: float | None, denominator: float | None) -> float | None:
        if numerator is None or denominator in (None, 0):
            return None
        return float(numerator) / abs(float(denominator)) * 100.0
