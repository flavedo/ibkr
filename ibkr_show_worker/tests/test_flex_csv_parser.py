from pathlib import Path

from worker.parsers.flex_csv_parser import parse_flex_csv

FIXTURE = Path(__file__).resolve().parents[1] / "worker" / "fixtures" / "daily_sample.csv"


def test_parse_flex_csv_extracts_sections_and_metadata() -> None:
    statement = parse_flex_csv(FIXTURE)

    assert statement.metadata.query_name == "Daily Snapshot"
    assert statement.metadata.from_date == "2026-04-17"
    assert statement.metadata.to_date == "2026-04-18"
    assert statement.metadata.account_ids == ["U1234567"]
    assert "POST" in statement.sections
    assert statement.get_section("TRNT") is not None
    assert len(statement.get_section("POST").rows) == 2
    assert statement.record_counts["DATA"] >= 1
