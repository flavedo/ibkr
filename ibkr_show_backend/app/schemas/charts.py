from pydantic import BaseModel


class EquityCurvePoint(BaseModel):
    report_date: str
    total_equity: float | None = None
    total_pnl: float | None = None
    net_cost: float | None = None
    realized_pnl: float | None = None
    daily_mtm: float | None = None
    daily_twr: float | None = None


class EquityCurveResponse(BaseModel):
    items: list[EquityCurvePoint]
