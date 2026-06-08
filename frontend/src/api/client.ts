const API_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')
const API_KEY = (import.meta.env.VITE_BDSA_API_KEY || '').trim()

export function getApiUrl(): string {
  return API_URL
}

/** Headers for authenticated API requests (when VITE_BDSA_API_KEY is set). */
export function apiHeaders(extra?: HeadersInit): Headers {
  const headers = new Headers(extra)
  if (API_KEY) {
    headers.set('X-API-Key', API_KEY)
  }
  return headers
}

/** Path under /api (e.g. `/collections`). Uses VITE_API_URL or same-origin (Vite/nginx proxy). */
export function apiPath(path: string): string {
  const p = path.startsWith('/') ? path : `/${path}`
  const withApi = p.startsWith('/api') ? p : `/api${p}`
  return API_URL ? `${API_URL}${withApi}` : withApi
}

export async function fetchApi<T = unknown>(path: string, init?: RequestInit): Promise<T> {
  const url = apiPath(path)
  const headers = apiHeaders(init?.headers)
  const res = await fetch(url, { ...init, headers })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API ${res.status}: ${text || res.statusText}`)
  }
  if (res.status === 204) {
    return undefined as T
  }
  return res.json() as Promise<T>
}
