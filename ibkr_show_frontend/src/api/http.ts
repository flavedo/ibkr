const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  (typeof window !== 'undefined'
    ? '/api'
    : 'http://localhost:8000')

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

function formatDetail(detail: unknown): string {
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === 'string') {
          return item
        }
        if (item && typeof item === 'object') {
          const message = 'msg' in item ? String(item.msg) : '请求参数非法'
          const location = Array.isArray((item as { loc?: unknown }).loc)
            ? (item as { loc: unknown[] }).loc.join('.')
            : ''
          return location ? `${location}: ${message}` : message
        }
        return String(item)
      })
      .join('；')
  }

  if (typeof detail === 'string') {
    return detail
  }

  return '请求失败'
}

export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers ?? undefined)
  if (init.body !== undefined && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    credentials: 'include',
    ...init,
    headers,
  })
  const contentType = response.headers.get('content-type') ?? ''
  const isJson = contentType.includes('application/json')
  const payload = isJson ? await response.json() : await response.text()

  if (!response.ok) {
    const detail =
      typeof payload === 'object' && payload !== null && 'detail' in payload
        ? formatDetail(payload.detail)
        : typeof payload === 'string'
          ? payload
          : `Request failed with status ${response.status}`
    throw new ApiError(detail, response.status)
  }

  return payload as T
}
