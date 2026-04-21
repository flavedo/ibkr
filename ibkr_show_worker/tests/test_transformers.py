from pathlib import Path

from worker.parsers.flex_csv_parser import FlexSection, FlexStatement, FlexStatementMetadata
from worker.parsers.flex_csv_parser import parse_flex_csv
from worker.parsers.transformers import (
    transform_daily_statement,
)

FIXTURE = Path(__file__).resolve().parents[1] / "worker" / "fixtures" / "daily_sample.csv"


def test_transform_daily_statement_generates_account_position_trade_and_cash_flow_documents() -> None:
    statement = parse_flex_csv(FIXTURE)
    transformed = transform_daily_statement(statement)

    assert len(transformed.account_documents) == 1
    assert transformed.account_documents[0]["account_id"] == "U1234567"
    assert transformed.account_documents[0]["report_date"] == "2026-04-18"

    assert len(transformed.position_documents) == 2
    first_position = transformed.position_documents[0]
    assert first_position["symbol"] == "AAPL"
    assert first_position["isin"] == "US0378331005"
    assert first_position["average_cost_price"] == 175.0
    assert first_position["total_realized_pnl"] == 120.5
    assert first_position["realized_pnl_percent"] == 120.5 / 17500 * 100
    assert first_position["total_unrealized_pnl"] == 80.25
    assert first_position["unrealized_pnl_percent"] == 80.25 / 17500 * 100
    assert first_position["total_fifo_pnl"] == 200.75
    assert first_position["previous_day_change_percent"] == (190 - 185) / 185 * 100

    assert len(transformed.trade_documents) == 1
    assert transformed.trade_documents[0]["unbc_total_commission"] == 1.2
    assert len(transformed.cash_flow_documents) == 1
    assert transformed.cash_flow_documents[0]["transaction_id"] == "CF1"
    assert transformed.cash_flow_documents[0]["flow_type"] == "Deposits/Withdrawals"
    assert transformed.cash_flow_documents[0]["amount"] == 5000.0
    assert len(transformed.price_history_documents) == 4
    assert transformed.price_history_documents[0]["symbol"] == "AAPL"
    assert transformed.price_history_documents[0]["close_price"] == 185.0
    assert transformed.price_history_documents[1]["previous_close_price"] == 185.0


def test_transform_daily_statement_supports_real_ibkr_fifo_headers() -> None:
    statement = parse_flex_csv(FIXTURE)
    fifo_row = statement.get_section("FIFO").rows[0]
    fifo_row.pop("RealizedPNL", None)
    fifo_row.pop("UnrealizedPNL", None)
    fifo_row.pop("TotalPNL", None)
    fifo_row["TotalRealizedPnl"] = "12.3"
    fifo_row["TotalUnrealizedPnl"] = "45.6"
    fifo_row["TotalFifoPnl"] = "57.9"

    transformed = transform_daily_statement(statement)

    assert transformed.position_documents[0]["total_realized_pnl"] == 12.3
    assert transformed.position_documents[0]["total_unrealized_pnl"] == 45.6
    assert transformed.position_documents[0]["total_fifo_pnl"] == 57.9


def test_transform_daily_statement_falls_back_to_mytd_realized_pnl_ytd_when_fifo_realized_is_zero() -> None:
    statement = parse_flex_csv(FIXTURE)
    fifo_row = statement.get_section("FIFO").rows[0]
    fifo_row["RealizedPNL"] = "0"
    fifo_row["TotalRealizedPnl"] = "0"

    transformed = transform_daily_statement(statement)

    assert transformed.position_documents[0]["total_realized_pnl"] == 800.0
    assert transformed.position_documents[0]["realized_pnl_ytd"] == 800.0
    assert transformed.position_documents[0]["realized_pnl_percent"] == 800.0 / 17500 * 100


def test_transform_daily_statement_generates_historical_account_documents_from_equt_rows() -> None:
    statement = FlexStatement(
        source_file=Path("/tmp/daily_history.csv"),
        metadata=FlexStatementMetadata(
            query_name="MyDailyData",
            from_date="2026-04-16",
            to_date="2026-04-17",
            account_ids=["U1234567"],
        ),
        sections={
            "EQUT": FlexSection(
                name="EQUT",
                headers=["ClientAccountID", "CurrencyPrimary", "ReportDate", "Cash", "Stock", "Total"],
                rows=[
                    {
                        "ClientAccountID": "U1234567",
                        "CurrencyPrimary": "USD",
                        "ReportDate": "20260416",
                        "Cash": "10",
                        "Stock": "90",
                        "Total": "100",
                    },
                    {
                        "ClientAccountID": "U1234567",
                        "CurrencyPrimary": "USD",
                        "ReportDate": "20260417",
                        "Cash": "20",
                        "Stock": "100",
                        "Total": "120",
                    },
                ],
            ),
            "FIFO": FlexSection(
                name="FIFO",
                headers=["ReportDate", "TotalRealizedPnl", "TotalUnrealizedPnl", "TotalFifoPnl"],
                rows=[
                    {
                        "ReportDate": "20260417",
                        "TotalRealizedPnl": "12",
                        "TotalUnrealizedPnl": "8",
                        "TotalFifoPnl": "20",
                    }
                ],
            ),
            "CNAV": FlexSection(
                name="CNAV",
                headers=["ToDate", "TWR"],
                rows=[{"ToDate": "20260417", "TWR": "1.2"}],
            ),
        },
        record_counts={},
    )

    transformed = transform_daily_statement(statement)

    assert len(transformed.account_documents) == 2
    assert transformed.account_documents[0]["report_date"] == "2026-04-16"
    assert transformed.account_documents[0]["total_equity"] == 100.0
    assert transformed.account_documents[1]["report_date"] == "2026-04-17"
    assert transformed.account_documents[1]["stock_value"] == 100.0
    assert transformed.account_documents[1]["fifo_total_pnl"] == 20.0
