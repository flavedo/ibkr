import { request } from './http'

export interface LoginResponse {
  token: string
}

export async function login(password: string): Promise<LoginResponse> {
  return request<LoginResponse>('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ password }),
  })
}
