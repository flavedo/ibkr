import { request } from './http'
import { withCache } from '@/utils/cache'

export interface EarningsEvent {
  symbol: string | null
  company: string
  marketcap: number | null
  event_name: string | null
  date_time: string | null
  timing: string | null
  eps_estimate: number | null
  reported_eps: number | null
  surprise_pct: number | null
}

export interface EconomicEvent {
  event_name: string | null
  region: string
  event_time: string | null
  for_period: string | null
  actual: number | null
  expected: number | null
  last: number | null
  revised: number | null
}

export interface EarningsCalendarResponse {
  items: EarningsEvent[]
}

export interface EconomicCalendarResponse {
  items: EconomicEvent[]
}

function toQueryString(params: Record<string, string | number | undefined | null>): string {
  const searchParams = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.set(key, String(value))
    }
  })
  const queryString = searchParams.toString()
  return queryString ? `?${queryString}` : ''
}

export function fetchEarningsCalendar(startDate: string, endDate: string): Promise<EarningsCalendarResponse> {
  return withCache(
    `earnings_${startDate}_${endDate}`,
    () => request<EarningsCalendarResponse>(`/api/financial-calendar/earnings${toQueryString({ start_date: startDate, end_date: endDate })}`)
  )
}

export function fetchEconomicCalendar(startDate: string, endDate: string): Promise<EconomicCalendarResponse> {
  return withCache(
    `economic_${startDate}_${endDate}`,
    () => request<EconomicCalendarResponse>(`/api/financial-calendar/economic-events${toQueryString({ start_date: startDate, end_date: endDate })}`)
  )
}
