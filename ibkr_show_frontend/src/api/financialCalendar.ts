import { request } from './http'
import { withCache } from '@/utils/cache'

export interface EarningsEvent {
  symbol: string
  name: string
  mcap: number
  exchange: string
  date: string
  is_estimate: boolean
  eps_avg: number | null
  eps_low: number | null
  eps_high: number | null
  rev_avg: number | null
  rev_low: number | null
  rev_high: number | null
  call_date: string
}

export interface EarningsCalendarResponse {
  items: EarningsEvent[]
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
