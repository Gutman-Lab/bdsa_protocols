import type { Protocol, ProtocolStorage } from 'bdsa-react-components'
import { fetchCollectionProtocols, putCollectionProtocols } from '../api/protocols'

function withType(
  protocols: Record<string, unknown>[],
  type: 'stain' | 'region' | 'block',
): Protocol[] {
  return protocols.map((p) => ({
    ...p,
    type,
    id: String(p.id ?? ''),
    name: String(p.name ?? ''),
  })) as Protocol[]
}

/**
 * Persists protocols to the bdsa_protocols backend (MongoDB per collection).
 */
export class ApiProtocolStorage implements ProtocolStorage {
  constructor(private readonly collectionId: string) {}

  async load(): Promise<Protocol[]> {
    if (!this.collectionId.trim()) {
      return []
    }
    const res = await fetchCollectionProtocols(this.collectionId)
    const payload = res.protocols
    return [
      ...withType(payload.stainProtocols ?? [], 'stain'),
      ...withType(payload.regionProtocols ?? [], 'region'),
      ...withType(payload.blockProtocols ?? [], 'block'),
    ]
  }

  async save(protocols: Protocol[]): Promise<void> {
    if (!this.collectionId.trim()) {
      throw new Error('Collection ID is required to save protocols')
    }
    const stainProtocols = protocols.filter((p) => p.type === 'stain')
    const regionProtocols = protocols.filter((p) => p.type === 'region')
    let blockProtocols = protocols.filter((p) => p.type === 'block') as Record<string, unknown>[]
    if (blockProtocols.length === 0) {
      const existing = await fetchCollectionProtocols(this.collectionId)
      blockProtocols = existing.protocols.blockProtocols ?? []
    }
    await putCollectionProtocols(this.collectionId, {
      stainProtocols,
      regionProtocols,
      blockProtocols,
      source: 'bdsa-protocols',
      version: '1.0',
    })
  }

  async clear(): Promise<void> {
    await putCollectionProtocols(this.collectionId, {
      stainProtocols: [],
      regionProtocols: [],
      blockProtocols: [],
      source: 'bdsa-protocols',
      version: '1.0',
    })
  }
}
