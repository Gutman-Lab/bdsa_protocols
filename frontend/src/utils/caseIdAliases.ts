/** Known external case ID alias systems (alternateIds keys). */

export interface CaseAliasSystem {
  key: string
  label: string
  hint: string
}

/** Always shown in the Case IDs table (even when empty). */
export const PRIMARY_CASE_ALIAS_SYSTEMS: CaseAliasSystem[] = [
  {
    key: 'nacc',
    label: 'NACC ID',
    hint: 'NACC case ID (clinical-metadata NACCID), e.g. U1234567',
  },
  {
    key: 'ndd',
    label: 'NDD ID',
    hint: 'Neuropathology data dictionary ID when distinct from NACC',
  },
]

const PRIMARY_KEYS = new Set(PRIMARY_CASE_ALIAS_SYSTEMS.map((s) => s.key))

export function aliasColumnLabel(systemKey: string): string {
  const known = PRIMARY_CASE_ALIAS_SYSTEMS.find((s) => s.key === systemKey)
  if (known) return known.label
  return systemKey
}

/** Extra alias systems present in data but not in the primary list. */
export function extraAliasSystems(caseMappings: { alternateIds?: Record<string, string> }[]): string[] {
  const systems = new Set<string>()
  for (const row of caseMappings) {
    for (const key of Object.keys(row.alternateIds ?? {})) {
      if (!PRIMARY_KEYS.has(key)) systems.add(key)
    }
  }
  return [...systems].sort()
}

export function allAliasSystems(
  caseMappings: { alternateIds?: Record<string, string> }[],
): CaseAliasSystem[] {
  const extras = extraAliasSystems(caseMappings).map((key) => ({
    key,
    label: aliasColumnLabel(key),
    hint: `External ID system "${key}"`,
  }))
  return [...PRIMARY_CASE_ALIAS_SYSTEMS, ...extras]
}
