/** Collection-level block (blocking) protocols — one physical block, many region protocols. */

export interface BlockProtocolSlot {
  regionProtocolId: string
  label?: string
}

export interface BlockProtocol {
  id: string
  type: 'block'
  name: string
  description?: string
  slots: BlockProtocolSlot[]
}

export function slugifyBlockId(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_|_$/g, '')
    .slice(0, 48)
}

export function suggestBlockProtocolId(
  collectionPrefix: string,
  name: string,
  existingIds: Iterable<string>,
): string {
  const taken = new Set(existingIds)
  const base = `${collectionPrefix}_block_${slugifyBlockId(name) || 'new'}`
  if (!taken.has(base)) return base
  for (let i = 2; i < 100; i += 1) {
    const candidate = `${base}_${i}`
    if (!taken.has(candidate)) return candidate
  }
  return `${base}_${Date.now()}`
}

export function normalizeBlockProtocol(raw: Record<string, unknown>): BlockProtocol {
  const slots = normalizeBlockSlots(raw)
  return {
    id: String(raw.id ?? ''),
    type: 'block',
    name: String(raw.name ?? raw.id ?? ''),
    description: raw.description ? String(raw.description) : undefined,
    slots,
  }
}

export function normalizeBlockSlots(raw: Record<string, unknown>): BlockProtocolSlot[] {
  const slots = raw.slots
  if (Array.isArray(slots)) {
    const out: BlockProtocolSlot[] = []
    for (const entry of slots) {
      if (!entry || typeof entry !== 'object') continue
      const row = entry as Record<string, unknown>
      const regionProtocolId = String(
        row.regionProtocolId ?? row.regionId ?? row.regionProtocol ?? '',
      ).trim()
      if (!regionProtocolId) continue
      const slot: BlockProtocolSlot = { regionProtocolId }
      if (row.label) slot.label = String(row.label).trim()
      out.push(slot)
    }
    if (out.length) return out
  }

  const regionProtocolIds = raw.regionProtocolIds
  if (Array.isArray(regionProtocolIds)) {
    return regionProtocolIds
      .map((id) => String(id ?? '').trim())
      .filter(Boolean)
      .map((regionProtocolId) => ({ regionProtocolId }))
  }

  return []
}

export function blockProtocolToPayload(block: BlockProtocol): Record<string, unknown> {
  return {
    id: block.id,
    type: 'block',
    name: block.name,
    description: block.description ?? undefined,
    slots: block.slots.map((slot) => ({
      regionProtocolId: slot.regionProtocolId,
      ...(slot.label ? { label: slot.label } : {}),
    })),
  }
}

export function regionProtocolLabel(
  regionProtocols: Record<string, unknown>[],
  regionProtocolId: string,
): string {
  const match = regionProtocols.find((p) => String(p.id) === regionProtocolId)
  if (!match) return regionProtocolId
  const name = String(match.name ?? '')
  return name ? `${name} (${regionProtocolId})` : regionProtocolId
}

export function formatBlockSlotsSummary(
  block: BlockProtocol,
  regionProtocols: Record<string, unknown>[],
): string {
  if (!block.slots.length) return '—'
  return block.slots
    .map((slot, index) => {
      const label = regionProtocolLabel(regionProtocols, slot.regionProtocolId)
      return slot.label ? `${index + 1}. ${slot.label} → ${label}` : `${index + 1}. ${label}`
    })
    .join('; ')
}
