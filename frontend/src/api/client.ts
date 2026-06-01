const API_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')

export function getApiUrl(): string {
  return API_URL
}

/** Path under /api (e.g. `/collections`). Uses VITE_API_URL or same-origin (Vite/nginx proxy). */
export function apiPath(path: string): string {
  const p = path.startsWith('/') ? path : `/${path}`
  const withApi = p.startsWith('/api') ? p : `/api${p}`
  return API_URL ? `${API_URL}${withApi}` : withApi
}

export async function fetchApi<T = unknown>(path: string, init?: RequestInit): Promise<T> {
  const url = apiPath(path)
  const res = await fetch(url, init)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API ${res.status}: ${text || res.statusText}`)
  }
  if (res.status === 204) {
    return undefined as T
  }
  return res.json() as Promise<T>
}
