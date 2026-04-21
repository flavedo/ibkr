import pytest

from app.utils.es_query_builder import build_date_range_filter, build_search_body, build_sort_clause
from app.utils.pagination import build_pagination


def test_build_pagination_clamps_page_size() -> None:
    from_value, size_value = build_pagination(page=2, page_size=500)

    assert from_value == 200
    assert size_value == 200


def test_build_sort_clause_uses_whitelist() -> None:
    sort_clause = build_sort_clause("symbol", "asc", {"symbol": "symbol", "value": "position_value"})

    assert sort_clause == [{"symbol": {"order": "asc", "missing": "_last"}}]


def test_build_sort_clause_rejects_unknown_field() -> None:
    with pytest.raises(ValueError):
        build_sort_clause("description", "asc", {"symbol": "symbol"})


def test_build_date_range_filter_generates_bounds() -> None:
    assert build_date_range_filter("report_date", "2026-01-01", "2026-04-17") == {
        "range": {"report_date": {"gte": "2026-01-01", "lte": "2026-04-17"}}
    }


def test_build_search_body_allows_custom_max_page_size() -> None:
    body = build_search_body(
        filters=[],
        sort=[{"report_date": {"order": "asc"}}],
        page=1,
        page_size=1000,
        max_page_size=5000,
        source_fields=["report_date"],
    )

    assert body["size"] == 1000
