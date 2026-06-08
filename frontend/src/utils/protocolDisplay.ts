/** Format protocol document fields for slide-mapping tables. */

export function formatProtocolField(value: unknown): string {
  if (value == null || value === '') return '—'
  if (Array.isArray(value)) return value.join(', ')
  return String(value)
}

export const REGION_SUMMARY_KEYS = [
  { key: 'regionType', label: 'Region type' },
  { key: 'hemisphere', label: 'Hemisphere' },
  { key: 'sliceThickness', label: 'Thickness (µm)' },
  { key: 'sliceOrientation', label: 'Orientation' },
  { key: 'landmarks', label: 'Landmarks' },
] as const

export const STAIN_SUMMARY_KEYS = [
  { key: 'stainType', label: 'Stain type' },
  { key: 'antibody', label: 'Antibody' },
  { key: 'phosphoSpecific', label: 'Phospho-specific' },
  { key: 'chromogen', label: 'Chromogen' },
  { key: 'chemistry', label: 'Chemistry' },
  { key: 'vendor', label: 'Vendor' },
] as const

export function protocolField(
  protocol: Record<string, unknown>,
  key: string,
): string {
  return formatProtocolField(protocol[key])
}

/** Extra keys on a protocol object not in the standard summary list. */
export function extraProtocolFields(
  protocol: Record<string, unknown>,
  knownKeys: readonly string[],
): Array<{ key: string; value: string }> {
  const skip = new Set([...knownKeys, 'id', 'type', 'name', 'description'])
  return Object.entries(protocol)
    .filter(([k, v]) => !skip.has(k) && v != null && v !== '')
    .map(([key, value]) => ({ key, value: formatProtocolField(value) }))
}
