export interface EquityCurvePoint {
  report_date: string
  total_equity: number | null
  total_pnl: number | null
  net_cost: number | null
  realized_pnl: number | null
}

export interface EquityCurveResponse {
  items: EquityCurvePoint[]
}
