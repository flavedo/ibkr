import { request } from './http'
import type { EquityCurveResponse } from '@/types/charts'

export function fetchEquityCurve(params: {
  start_date?: string
  end_date?: string
} = {}): Promise<EquityCurveResponse> {
  const searchParams = new URLSearchParams()
  if (params.start_date) {
    searchParams.set('start_date', params.start_date)
  }
  if (params.end_date) {
    searchParams.set('end_date', params.end_date)
  }
  const queryString = searchParams.toString()
  return request<EquityCurveResponse>(`/api/charts/equity-curve${queryString ? `?${queryString}` : ''}`)
}
