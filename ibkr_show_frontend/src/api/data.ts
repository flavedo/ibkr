import { request } from './http'

export async function triggerDataRefresh(): Promise<{ success: boolean; result?: unknown }> {
  return request('/api/data/refresh', { method: 'POST' })
}

export async function importCSV(files: File[]): Promise<{ success: boolean; results?: Record<string, unknown>; errors?: Record<string, string> }> {
  const formData = new FormData()
  files.forEach((file) => {
    formData.append('files', file)
  })

  const token = localStorage.getItem('auth_token')
  const headers = new Headers()
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch('/api/data/import-csv', {
    method: 'POST',
    body: formData,
    headers,
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function clearData(): Promise<{ success: boolean; deleted?: Record<string, number | string> }> {
  return request('/api/data/clear', { method: 'POST' })
}
