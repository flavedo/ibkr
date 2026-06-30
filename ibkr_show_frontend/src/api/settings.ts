import { request } from './http'

export interface SystemSettings {
  enabled: boolean
  push_time: string
  smtp_server: string
  smtp_port: number
  smtp_username: string
  smtp_password: string
  sender_email: string
  target_email: string
  fetch_enabled: boolean
  fetch_time: string
}

export interface TestSendResult {
  success: boolean
  message: string
}

export function fetchSettings(): Promise<SystemSettings> {
  return request<SystemSettings>('/api/settings')
}

export function updateSettings(settings: SystemSettings): Promise<SystemSettings> {
  return request<SystemSettings>('/api/settings', {
    method: 'PUT',
    body: JSON.stringify(settings),
  })
}

export function sendTestEmail(settings: SystemSettings): Promise<TestSendResult> {
  return request<TestSendResult>('/api/settings/push/test-send', {
    method: 'POST',
    body: JSON.stringify(settings),
  })
}

export function triggerDailyPush(): Promise<TestSendResult> {
  return request<TestSendResult>('/api/settings/push/trigger', {
    method: 'POST',
  })
}
