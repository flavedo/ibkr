from typing import Any

from app.clients.es_client import ElasticsearchClient
from app.core.config import Settings
from app.schemas.common import PaginationInfo
from app.schemas.dividends import DividendItem, DividendListResponse, DividendSummaryResponse


class DividendService:
    def __init__(self, es_client: ElasticsearchClient, settings: Settings) -> None:
        self.es_client = es_client
        self.settings = settings

    def list_dividends(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        symbol: str | None = None,
        sort_by: str = "date_time",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> DividendListResponse:
        must_clauses: list[dict[str, Any]] = [
            {"term": {"flow_type": "Dividend"}},
            {"range": {"amount": {"gt": 0}}},
        ]

        if start_date:
            must_clauses.append({"range": {"date_time": {"gte": start_date}}})
        if end_date:
            must_clauses.append({"range": {"date_time": {"lte": end_date}}})
        if symbol:
            must_clauses.append({"term": {"symbol": symbol.upper()}})

        response = self.es_client.search(
            index=self.settings.es_cash_flow_index,
            body={
                "size": page_size,
                "from": (page - 1) * page_size,
                "query": {"bool": {"must": must_clauses}},
                "sort": [{sort_by: {"order": sort_order}}],
            },
        )

        hits = response.get("hits", {})
        total = hits.get("total", {}).get("value", 0)
        items = [DividendItem(**hit["_source"]) for hit in hits.get("hits", [])]

        return DividendListResponse(
            items=items,
            pagination=PaginationInfo(
                page=page,
                page_size=page_size,
                total=total,
                total_pages=(total + page_size - 1) // page_size if total > 0 else 0,
            ),
        )

    def summarize_dividends(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        symbol: str | None = None,
    ) -> DividendSummaryResponse:
        must_clauses: list[dict[str, Any]] = [
            {"term": {"flow_type": "Dividend"}},
            {"range": {"amount": {"gt": 0}}},
        ]

        if start_date:
            must_clauses.append({"range": {"date_time": {"gte": start_date}}})
        if end_date:
            must_clauses.append({"range": {"date_time": {"lte": end_date}}})
        if symbol:
            must_clauses.append({"term": {"symbol": symbol.upper()}})

        response = self.es_client.search(
            index=self.settings.es_cash_flow_index,
            body={
                "size": 0,
                "query": {"bool": {"must": must_clauses}},
                "aggs": {
                    "total_amount": {"sum": {"field": "amount"}},
                    "total_gross_amount": {"sum": {"field": "gross_amount"}},
                    "by_symbol": {"terms": {"field": "symbol.keyword", "size": 100}, "aggs": {"total": {"sum": {"field": "amount"}}}},
                },
            },
        )

        aggs = response.get("aggregations", {})
        by_symbol_buckets = aggs.get("by_symbol", {}).get("buckets", [])
        by_symbol = {bucket["key"]: bucket["total"]["value"] for bucket in by_symbol_buckets}

        return DividendSummaryResponse(
            record_count=response.get("hits", {}).get("total", {}).get("value", 0),
            total_amount=aggs.get("total_amount", {}).get("value"),
            total_gross_amount=aggs.get("total_gross_amount", {}).get("value"),
            by_symbol=by_symbol,
        )