export interface EquityCurvePoint {
  report_date: string
  total_equity: number | null
  total_pnl: number | null
  net_cost: number | null
  realized_pnl: number | null
  daily_mtm: number | null
  daily_twr: number | null
  cnav_twr: number | null
}

export interface EquityCurveResponse {
  items: EquityCurvePoint[]
}
