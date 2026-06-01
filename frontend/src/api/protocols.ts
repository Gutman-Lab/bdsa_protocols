import { fetchApi } from './client'

export interface ProtocolsPayload {
  stainProtocols: Record<string, unknown>[]
  regionProtocols: Record<string, unknown>[]
  blockProtocols?: Record<string, unknown>[]
  lastUpdated?: string
  source?: string
  version?: string
}

export interface ProtocolsResponse {
  success?: boolean
  collection_id: string
  protocols: ProtocolsPayload
}

export interface CollectionSummary {
  collection_id: string
  display_name: string
  number: number
}

export interface CollectionsListResponse {
  collection_ids: string[]
  collections?: CollectionSummary[]
}

export function fetchCollections(): Promise<CollectionsListResponse> {
  return fetchApi('/collections')
}

export function updateCollectionDisplayName(
  collectionId: string,
  displayName: string,
): Promise<{ collection_id: string; display_name: string }> {
  return fetchApi(`/collections/${encodeURIComponent(collectionId)}/metadata`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ display_name: displayName }),
  })
}

export function fetchCollectionProtocols(collectionId: string): Promise<ProtocolsResponse> {
  return fetchApi(`/collections/${encodeURIComponent(collectionId)}/protocols`)
}

export function putCollectionProtocols(
  collectionId: string,
  payload: ProtocolsPayload,
): Promise<ProtocolsResponse> {
  return fetchApi(`/collections/${encodeURIComponent(collectionId)}/protocols`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      stainProtocols: payload.stainProtocols,
      regionProtocols: payload.regionProtocols,
      blockProtocols: payload.blockProtocols ?? [],
      source: payload.source ?? 'bdsa-protocols',
      version: payload.version ?? '1.0',
    }),
  })
}
