const API_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '') || 'http://localhost:8000'
const API_KEY = (import.meta.env.VITE_BDSA_API_KEY || '').trim()

export function getApiUrl(): string {
  return API_URL
}

function apiHeaders(extra?: HeadersInit): Headers {
  const headers = new Headers(extra)
  if (API_KEY) {
    headers.set('X-API-Key', API_KEY)
  }
  return headers
}

async function apiFetch(url: string, init?: RequestInit): Promise<Response> {
  return fetch(url, { ...init, headers: apiHeaders(init?.headers) })
}

export async function fetchApi<T = unknown>(path: string): Promise<T> {
  const url = `${API_URL}${path.startsWith('/') ? path : `/${path}`}`
  const res = await apiFetch(url)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API ${res.status}: ${text || res.statusText}`)
  }
  return res.json() as Promise<T>
}

export async function fetchCollections(): Promise<{ collection_ids: string[] }> {
  return fetchApi('/api/collections')
}

export interface BackupStatus {
  backupDirConfigured: boolean
  backupDir: string | null
}

export async function fetchBackupStatus(): Promise<BackupStatus> {
  return fetchApi('/api/admin/backup/status')
}

function filenameFromContentDisposition(header: string | null): string | null {
  if (!header) return null
  const match = /filename="?([^";\n]+)"?/i.exec(header)
  return match?.[1] ?? null
}

/** Download full Mongo export as a JSON file in the browser. */
export async function downloadMongoBackup(): Promise<{ filename: string; counts: Record<string, number> }> {
  const url = `${API_URL}/api/admin/backup`
  const res = await apiFetch(url)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API ${res.status}: ${text || res.statusText}`)
  }
  const text = await res.text()
  const parsed = JSON.parse(text) as { counts?: Record<string, number> }
  const filename =
    filenameFromContentDisposition(res.headers.get('Content-Disposition')) ??
    `bdsa-backup-${new Date().toISOString().replace(/[:.]/g, '-')}.json`

  const blob = new Blob([text], { type: 'application/json' })
  const objectUrl = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = objectUrl
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(objectUrl)

  return { filename, counts: parsed.counts ?? {} }
}

/** Write backup JSON on the API host (requires BDSA_BACKUP_DIR). */
export async function saveMongoBackupOnServer(): Promise<{
  path: string
  filename: string
  counts: Record<string, number>
}> {
  const url = `${API_URL}/api/admin/backup/save`
  const res = await apiFetch(url, { method: 'POST' })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API ${res.status}: ${text || res.statusText}`)
  }
  return res.json() as Promise<{
    path: string
    filename: string
    counts: Record<string, number>
  }>
}

export async function deleteCollection(collectionId: string) {
  const url = `${API_URL}/api/collections/${encodeURIComponent(collectionId)}?confirm=true`
  const res = await apiFetch(url, { method: 'DELETE' })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API ${res.status}: ${text || res.statusText}`)
  }
  return res.json()
}

export async function renameCollection(collectionId: string, newCollectionId: string) {
  const url = `${API_URL}/api/collections/${encodeURIComponent(collectionId)}/rename`
  const res = await apiFetch(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ new_collection_id: newCollectionId }),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API ${res.status}: ${text || res.statusText}`)
  }
  return res.json()
}

export async function fetchProtocols(collectionId: string) {
  return fetchApi(`/api/collections/${collectionId}/protocols`)
}

export async function fetchCaseIdMappings(collectionId: string) {
  return fetchApi(`/api/collections/${collectionId}/case-id-mappings`)
}

export async function fetchPatientIdMappings(collectionId: string) {
  return fetchApi(`/api/collections/${collectionId}/patient-id-mappings`)
}

export async function fetchSlides(collectionId: string) {
  return fetchApi(`/api/collections/${collectionId}/slides`)
}

export interface Block2RegionCaseEntry {
  block2region: Record<string, string>
  mapping_source?: string | null
  validated?: boolean
  case_status?: string | null
  lastUpdated?: string | null
}

export async function fetchBlock2Region(collectionId: string) {
  return fetchApi<{ collection_id: string; by_case: Record<string, Block2RegionCaseEntry> }>(
    `/api/collections/${collectionId}/block2region`
  )
}

/** Lightweight stats for the Block → Region panel (patients with maps, total pairs, validated). */
export async function fetchBlock2RegionStats(collectionId: string) {
  return fetchApi<{
    casesWithMaps: number
    totalPairs: number
    validatedCount: number
    caseIds: string[]
  }>(`/api/collections/${collectionId}/block2region/stats`)
}

/** Fetch block2region for a single case (no need to load all). */
export async function fetchBlock2RegionOne(
  collectionId: string,
  caseId: string
) {
  return fetchApi<{
    success: boolean
    collection_id: string
    case_id: string
    block2region: Block2RegionCaseEntry | null
  }>(`/api/collections/${collectionId}/cases/${encodeURIComponent(caseId)}/block2region`)
}

export async function fetchCasesForCollection(collectionId: string) {
  return fetchApi<{ collection_id: string; case_ids: string[] }>(
    `/api/collections/${collectionId}/cases`
  )
}

export interface Block2RegionVersionEntry {
  version: number
  block2region: Record<string, string>
  mapping_source?: string | null
  validated?: boolean
  createdAt?: string | null
}

export async function fetchBlock2RegionVersions(collectionId: string, caseId: string) {
  return fetchApi<{
    success: boolean
    collection_id: string
    case_id: string
    versions: Block2RegionVersionEntry[]
  }>(`/api/collections/${collectionId}/cases/${encodeURIComponent(caseId)}/block2region/versions`)
}

export async function restoreBlock2RegionVersion(
  collectionId: string,
  caseId: string,
  version: number
) {
  const url = `${API_URL}/api/collections/${collectionId}/cases/${encodeURIComponent(caseId)}/block2region/restore`
  const res = await apiFetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ version }),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API ${res.status}: ${text || res.statusText}`)
  }
  return res.json() as Promise<{ success: boolean; collection_id: string; case_id: string; block2region: Block2RegionCaseEntry | null }>
}
