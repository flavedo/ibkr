from worker.parsers.transformers import (
    build_account_snapshot_id,
    build_cash_flow_record_id,
    build_position_snapshot_id,
    build_price_history_record_id,
    build_trade_record_id,
)


def test_account_snapshot_id_is_deterministic() -> None:
    assert build_account_snapshot_id("U1234567", "2026-04-18") == build_account_snapshot_id(
        "U1234567",
        "2026-04-18",
    )


def test_position_snapshot_id_is_deterministic() -> None:
    first = build_position_snapshot_id("U1234567", "2026-04-18", "STK", "265598")
    second = build_position_snapshot_id("U1234567", "2026-04-18", "STK", "265598")
    assert first == second


def test_trade_record_id_prefers_transaction_id() -> None:
    first = build_trade_record_id("U1234567", "2026-04-18", "AAPL", "T1", "BUY", 10, "TX1")
    second = build_trade_record_id("U1234567", "2026-04-18", "AAPL", "T1", "BUY", 10, "TX1")
    assert first == second == "TX1"


def test_cash_flow_record_id_prefers_transaction_id() -> None:
    first = build_cash_flow_record_id("U1234567", "2026-04-18T12:00:00Z", 5000, "CF1")
    second = build_cash_flow_record_id("U1234567", "2026-04-18T12:00:00Z", 5000, "CF1")
    assert first == second == "CF1"


def test_price_history_record_id_is_deterministic() -> None:
    first = build_price_history_record_id("U1234567", "2026-04-18", "STK", "265598")
    second = build_price_history_record_id("U1234567", "2026-04-18", "STK", "265598")
    assert first == second
