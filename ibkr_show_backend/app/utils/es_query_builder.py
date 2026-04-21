from app.utils.pagination import build_pagination


def build_sort_clause(
    sort_by: str,
    sort_order: str,
    whitelist: dict[str, str],
) -> list[dict]:
    if sort_by not in whitelist:
        raise ValueError(f"Unsupported sort field: {sort_by}")
    if sort_order not in {"asc", "desc"}:
        raise ValueError(f"Unsupported sort order: {sort_order}")
    return [{whitelist[sort_by]: {"order": sort_order, "missing": "_last"}}]


def build_date_range_filter(field: str, start_date: str | None, end_date: str | None) -> dict | None:
    if not start_date and not end_date:
        return None

    range_query: dict[str, str] = {}
    if start_date:
        range_query["gte"] = start_date
    if end_date:
        range_query["lte"] = end_date

    return {"range": {field: range_query}}


def build_term_filter(field: str, value: str | None) -> dict | None:
    if not value:
        return None
    return {"term": {field: value}}


def build_search_body(
    filters: list[dict],
    sort: list[dict],
    page: int,
    page_size: int,
    source_fields: list[str],
    max_page_size: int = 200,
) -> dict:
    from_value, size_value = build_pagination(page=page, page_size=page_size, max_page_size=max_page_size)
    return {
        "query": {"bool": {"filter": filters or [{"match_all": {}}]}},
        "sort": sort,
        "from": from_value,
        "size": size_value,
        "_source": source_fields,
        "track_total_hits": True,
    }
