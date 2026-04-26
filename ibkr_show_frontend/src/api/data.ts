export async function triggerDataRefresh(): Promise<{ success: boolean; result?: unknown }> {
  const response = await fetch('/api/data/refresh', { method: 'POST' })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export async function importCSV(file: File): Promise<{ success: boolean; result?: unknown }> {
  const formData = new FormData()
  formData.append('file', file)

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
