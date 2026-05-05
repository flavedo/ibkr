export async function triggerDataRefresh(): Promise<{ success: boolean; result?: unknown }> {
  const response = await fetch('/api/data/refresh', { method: 'POST' })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function importCSV(files: File[]): Promise<{ success: boolean; results?: Record<string, unknown>; errors?: Record<string, string> }> {
  const formData = new FormData()
  files.forEach((file) => {
    formData.append('files', file)
  })

  const response = await fetch('/api/data/import-csv', {
    method: 'POST',
    body: formData,
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function clearData(): Promise<{ success: boolean; deleted?: Record<string, number | string> }> {
  const response = await fetch('/api/data/clear', { method: 'POST' })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}
