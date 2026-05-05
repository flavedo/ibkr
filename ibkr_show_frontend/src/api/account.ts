import { request } from './http'
import type { AccountOverview, ExchangeRate, LatestReportDate } from '@/types/account'

export function fetchAccountOverview(): Promise<AccountOverview> {
  return request<AccountOverview>('/api/account/overview')
}

export function fetchLatestReportDate(): Promise<LatestReportDate> {
  return request<LatestReportDate>('/api/account/latest-report-date')
}

export function fetchExchangeRate(fromCurrency = 'USD', toCurrency = 'CNH'): Promise<ExchangeRate> {
  return request<ExchangeRate>(`/api/account/exchange-rate?from_currency=${fromCurrency}&to_currency=${toCurrency}`)
}
