import { request } from './http'

export interface HealthResponse {
  status: string
  service: string
}

export async function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health')
}
