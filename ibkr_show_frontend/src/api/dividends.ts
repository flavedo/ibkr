import { request } from './http'
import type { PaginationInfo } from '@/types/common'

export interface DividendItem {
  account_id: string
  currency: string | null
  symbol: string | null
  description: string | null
  date_time: string | null
  settle_date: string | null
  amount: number | null
  gross_amount: number | null
  tax: number | null
  fx_rate_to_base: number | null
  amount_in_base: number | null
  flow_direction: string | null
  flow_type: string | null
  dividend_type: string | null
  transaction_id: string | null
  report_date: string | null
  activity_code: string | null
  activity_description: string | null
  level_of_detail: string | null
}

export interface DividendListResponse {
  items: DividendItem[]
  pagination: PaginationInfo
}

export interface DividendSummaryResponse {
  record_count: number
  total_amount: number | null
  total_gross_amount: number | null
  by_symbol: Record<string, number>
}

export interface DividendQuery {
  start_date?: string
  end_date?: string
  symbol?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
  page?: number
  page_size?: number
}

function toQueryString(params: Record<string, string | number | undefined | null> | DividendQuery): string {
  const searchParams = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') {
      searchParams.set(key, String(value))
    }
  })
  const queryString = searchParams.toString()
  return queryString ? `?${queryString}` : ''
}

export function fetchDividends(params: DividendQuery): Promise<DividendListResponse> {
  return request<DividendListResponse>(`/api/dividends${toQueryString(params)}`)
}

export function fetchDividendSummary(params: Omit<DividendQuery, 'sort_by' | 'sort_order' | 'page' | 'page_size'>): Promise<DividendSummaryResponse> {
  return request<DividendSummaryResponse>(`/api/dividends/summary${toQueryString(params)}`)
}