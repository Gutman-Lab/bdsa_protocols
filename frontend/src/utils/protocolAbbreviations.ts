/** Abbreviation helpers for region/stain protocols (filename tokens). */

export interface ProtocolLike {
  id?: unknown
  name?: unknown
  type?: unknown
  abbreviation?: unknown
  schemaStainKey?: unknown
  stainType?: unknown
  displayName?: unknown
  [key: string]: unknown
}

export interface AbbreviationCollisionGroup {
  /** Display form of the abbreviation (first seen casing). */
  abbreviation: string
  /** Normalized key used for grouping. */
  key: string
  protocolIds: string[]
  names: string[]
}

export interface AbbreviationAnalysis {
  collisions: AbbreviationCollisionGroup[]
  /** Region protocols with no abbreviation set. */
  missing: { protocolIds: string[]; names: string[] }
  /** Protocol ids that participate in a collision. */
  collidingIds: Set<string>
}

export function normalizeAbbreviation(raw: unknown): string | null {
  if (raw == null) return null
  const s = String(raw).trim()
  if (!s) return null
  return s
}

/** Case-insensitive key for collision grouping. */
export function abbreviationKey(raw: unknown): string | null {
  const s = normalizeAbbreviation(raw)
  return s ? s.toLocaleLowerCase() : null
}

/** Filename token for a region protocol. */
export function regionAbbreviation(protocol: ProtocolLike): string | null {
  return normalizeAbbreviation(protocol.abbreviation)
}

/**
 * Filename token for a stain protocol.
 * Prefer explicit abbreviation, then schemaStainKey, then stainType.
 */
export function stainAbbreviation(protocol: ProtocolLike): string | null {
  return (
    normalizeAbbreviation(protocol.abbreviation) ??
    normalizeAbbreviation(protocol.schemaStainKey) ??
    normalizeAbbreviation(protocol.stainType)
  )
}

function protocolLabel(protocol: ProtocolLike): string {
  const display = normalizeAbbreviation(protocol.displayName)
  if (display) return display
  const name = normalizeAbbreviation(protocol.name)
  if (name) return name
  return String(protocol.id ?? '(unknown)')
}

function findCollisions(
  protocols: ProtocolLike[],
  tokenFn: (p: ProtocolLike) => string | null,
): AbbreviationAnalysis {
  const byKey = new Map<string, AbbreviationCollisionGroup>()
  const missingIds: string[] = []
  const missingNames: string[] = []

  for (const protocol of protocols) {
    const id = String(protocol.id ?? '')
    const label = protocolLabel(protocol)
    const token = tokenFn(protocol)
    const key = abbreviationKey(token)
    if (!key || !token) {
      if (id) {
        missingIds.push(id)
        missingNames.push(label)
      }
      continue
    }
    const existing = byKey.get(key)
    if (existing) {
      if (id && !existing.protocolIds.includes(id)) {
        existing.protocolIds.push(id)
        existing.names.push(label)
      }
    } else {
      byKey.set(key, {
        abbreviation: token,
        key,
        protocolIds: id ? [id] : [],
        names: [label],
      })
    }
  }

  const collisions = [...byKey.values()].filter((g) => g.protocolIds.length > 1)
  const collidingIds = new Set<string>()
  for (const g of collisions) {
    for (const id of g.protocolIds) collidingIds.add(id)
  }

  return {
    collisions,
    missing: { protocolIds: missingIds, names: missingNames },
    collidingIds,
  }
}

export function analyzeRegionAbbreviations(
  protocols: ProtocolLike[],
): AbbreviationAnalysis {
  return findCollisions(protocols, regionAbbreviation)
}

export function analyzeStainAbbreviations(
  protocols: ProtocolLike[],
): AbbreviationAnalysis {
  return findCollisions(protocols, stainAbbreviation)
}

export function formatCollisionSummary(
  kind: 'region' | 'stain',
  groups: AbbreviationCollisionGroup[],
): string[] {
  return groups.map((g) => {
    const labels = g.names.length ? g.names.join(', ') : g.protocolIds.join(', ')
    const noun = kind === 'region' ? 'Region' : 'Stain'
    return `${noun} abbreviation "${g.abbreviation}" used by: ${labels}`
  })
}

export interface BlockSlotCollision {
  blockId: string
  blockName: string
  /** Abbreviation groups that collide among this block's region slots. */
  collisions: AbbreviationCollisionGroup[]
}

/**
 * Warn when a single block's slots resolve to region protocols that share
 * the same abbreviation (ambiguous slide/filename tokens from that cassette).
 */
export function analyzeBlockSlotAbbreviationCollisions(
  blocks: Array<{ id: string; name: string; slots: Array<{ regionProtocolId: string }> }>,
  regionProtocols: ProtocolLike[],
): {
  blockCollisions: BlockSlotCollision[]
  collidingBlockIds: Set<string>
  lines: string[]
} {
  const byRegionId = new Map<string, ProtocolLike>()
  for (const p of regionProtocols) {
    const id = String(p.id ?? '')
    if (id) byRegionId.set(id, p)
  }

  const blockCollisions: BlockSlotCollision[] = []
  const collidingBlockIds = new Set<string>()
  const lines: string[] = []

  for (const block of blocks) {
    const slotRegions: ProtocolLike[] = []
    for (const slot of block.slots) {
      const region = byRegionId.get(slot.regionProtocolId)
      if (region) {
        slotRegions.push(region)
      } else {
        // Unknown id — still include a stub so missing abbrev isn't confused with collision
        slotRegions.push({ id: slot.regionProtocolId, name: slot.regionProtocolId })
      }
    }
    const analysis = analyzeRegionAbbreviations(slotRegions)
    if (analysis.collisions.length === 0) continue
    blockCollisions.push({
      blockId: block.id,
      blockName: block.name,
      collisions: analysis.collisions,
    })
    collidingBlockIds.add(block.id)
    for (const g of analysis.collisions) {
      const labels = g.names.length ? g.names.join(', ') : g.protocolIds.join(', ')
      lines.push(
        `Block "${block.name || block.id}": abbreviation "${g.abbreviation}" used by slots: ${labels}`,
      )
    }
  }

  return { blockCollisions, collidingBlockIds, lines }
}
