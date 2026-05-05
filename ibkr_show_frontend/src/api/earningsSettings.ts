import { request } from './http'

export interface EarningsPushSettings {
  enabled: boolean
  push_time: string
  smtp_server: string
  smtp_port: number
  smtp_username: string
  smtp_password: string
  sender_email: string
  target_email: string
}

export interface TestSendResult {
  success: boolean
  message: string
}

export function fetchPushSettings(): Promise<EarningsPushSettings> {
  return request<EarningsPushSettings>('/api/earnings-settings/push')
}

export function updatePushSettings(settings: EarningsPushSettings): Promise<EarningsPushSettings> {
  return request<EarningsPushSettings>('/api/earnings-settings/push', {
    method: 'PUT',
    body: JSON.stringify(settings),
  })
}

export function sendTestEmail(settings: EarningsPushSettings): Promise<TestSendResult> {
  return request<TestSendResult>('/api/earnings-settings/push/test-send', {
    method: 'POST',
    body: JSON.stringify(settings),
  })
}

export function triggerDailyPush(): Promise<TestSendResult> {
  return request<TestSendResult>('/api/earnings-settings/push/trigger', {
    method: 'POST',
  })
}
