import { useMemo, useState } from 'react'
import { hasApiKey } from '../../api/client'
import {
  mergeCaseIdMappings,
  type CaseIdMappingItem,
  type PatientIdMappingItem,
} from '../../api/idMappings'
import { allAliasSystems } from '../../utils/caseIdAliases'
import { CaseIdAliasCell } from './CaseIdAliasCell'

function matchesQuery(query: string, ...values: (string | null | undefined)[]): boolean {
  if (!query) return true
  const q = query.trim().toLowerCase()
  if (!q) return true
  return values.some((v) => (v ?? '').toLowerCase().includes(q))
}

function RegistryMeta({
  institutionId,
  lastUpdated,
  source,
  count,
  aliasStats,
}: {
  institutionId?: string
  lastUpdated?: string | null
  source?: string
  count: number
  aliasStats: { system: string; label: string; filled: number }[]
}) {
  return (
    <p className="slide-mappings-section-desc">
      {count} mapping{count === 1 ? '' : 's'}
      {institutionId ? (
        <>
          {' '}
          · institution <code>{institutionId}</code>
        </>
      ) : null}
      {aliasStats.map(({ system, label, filled }) =>
        filled > 0 ? (
          <span key={system}>
            {' '}
            · {filled} with {label}
          </span>
        ) : null,
      )}
      {lastUpdated ? (
        <>
          {' '}
          · updated {new Date(lastUpdated).toLocaleString()}
        </>
      ) : null}
      {source ? (
        <>
          {' '}
          · source <code>{source}</code>
        </>
      ) : null}
    </p>
  )
}

export function CaseIdMappingsTab({
  collectionId,
  caseMappings,
  caseInstitutionId,
  caseLastUpdated,
  caseSource,
  patientMappings,
  patientInstitutionId,
  patientLastUpdated,
  patientSource,
  onMappingsUpdated,
}: {
  collectionId: string
  caseMappings: CaseIdMappingItem[]
  caseInstitutionId?: string
  caseLastUpdated?: string | null
  caseSource?: string
  patientMappings: PatientIdMappingItem[]
  patientInstitutionId?: string
  patientLastUpdated?: string | null
  patientSource?: string
  onMappingsUpdated?: () => void
}) {
  const [search, setSearch] = useState('')
  const [savingKey, setSavingKey] = useState<string | null>(null)
  const canEdit = hasApiKey()

  const aliasSystems = useMemo(() => allAliasSystems(caseMappings), [caseMappings])

  const aliasStats = useMemo(
    () =>
      aliasSystems.map((system) => ({
        system: system.key,
        label: system.label,
        filled: caseMappings.filter((row) => row.alternateIds?.[system.key]).length,
      })),
    [aliasSystems, caseMappings],
  )

  const filteredCaseMappings = useMemo(() => {
    const rows = caseMappings.filter((row) => {
      const alternateValues = Object.values(row.alternateIds ?? {})
      return matchesQuery(search, row.localCaseId, row.bdsaCaseId, ...alternateValues)
    })
    return [...rows].sort((a, b) => a.localCaseId.localeCompare(b.localCaseId))
  }, [caseMappings, search])

  const filteredPatientMappings = useMemo(() => {
    const rows = patientMappings.filter((row) =>
      matchesQuery(search, row.localPatientId, row.bdsaPatientId),
    )
    return [...rows].sort((a, b) => a.localPatientId.localeCompare(b.localPatientId))
  }, [patientMappings, search])

  const showPatientSection = patientMappings.length > 0

  const saveAlias = async (
    row: CaseIdMappingItem,
    systemKey: string,
    nextValue: string | null,
  ) => {
    const cellKey = `${row.localCaseId}:${systemKey}`
    setSavingKey(cellKey)
    try {
      await mergeCaseIdMappings(collectionId, {
        institutionId: caseInstitutionId ?? '001',
        mappings: [
          {
            localCaseId: row.localCaseId,
            bdsaCaseId: row.bdsaCaseId,
            alternateIds: { [systemKey]: nextValue ?? '' },
          },
        ],
        source: 'bdsa-protocols-ui',
      })
      onMappingsUpdated?.()
    } finally {
      setSavingKey(null)
    }
  }

  return (
    <div>
      <div className="slide-mappings-search-bar">
        <label htmlFor="case-id-search">Filter</label>
        <input
          id="case-id-search"
          type="search"
          className="slide-mappings-search-input"
          placeholder="Local, BDSA, or NACC ID…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        {search && (
          <button
            type="button"
            className="slide-mappings-search-clear"
            onClick={() => setSearch('')}
          >
            Clear
          </button>
        )}
      </div>

      <section className="slide-mappings-section">
        <h3>Case ID registry (localCaseId → bdsaCaseId)</h3>
        <p className="slide-mappings-section-desc">
          Canonical BDSA case IDs use format <code>BDSA-{'{institution}'}-{'{sequence}'}</code>{' '}
          (e.g. <code>BDSA-002-00001</code> for U. Kentucky). Use the alias columns to attach
          external IDs such as <strong>NACC ID</strong> (<code>alternateIds.nacc</code>, linked to
          clinical-metadata <code>NACCID</code>).
        </p>
        {!canEdit && (
          <p className="slide-mappings-section-desc case-id-readonly-hint">
            Alias editing requires <code>VITE_BDSA_API_KEY</code> in the frontend environment.
            View and filter still work without it.
          </p>
        )}
        <RegistryMeta
          institutionId={caseInstitutionId}
          lastUpdated={caseLastUpdated}
          source={caseSource}
          count={filteredCaseMappings.length}
          aliasStats={aliasStats}
        />
        {caseMappings.length === 0 ? (
          <p className="slide-mappings-empty">No case ID mappings stored for this center yet.</p>
        ) : filteredCaseMappings.length === 0 ? (
          <p className="slide-mappings-empty">No rows match your filter.</p>
        ) : (
          <div className="slide-mappings-table-wrap">
            <table className="slide-mappings-table case-id-mappings-table">
              <thead>
                <tr>
                  <th>Local case ID</th>
                  <th>BDSA case ID</th>
                  {aliasSystems.map((system) => (
                    <th key={system.key} title={system.hint}>
                      {system.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filteredCaseMappings.map((row) => (
                  <tr key={row.localCaseId}>
                    <td>
                      <code>{row.localCaseId}</code>
                    </td>
                    <td>
                      <code>{row.bdsaCaseId}</code>
                    </td>
                    {aliasSystems.map((system) => {
                      const cellKey = `${row.localCaseId}:${system.key}`
                      return (
                        <td key={system.key} className="case-alias-td">
                          <CaseIdAliasCell
                            value={row.alternateIds?.[system.key]}
                            label={system.label}
                            hint={system.hint}
                            disabled={!canEdit}
                            saving={savingKey === cellKey}
                            onSave={(next) => saveAlias(row, system.key, next)}
                          />
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {showPatientSection && (
        <section className="slide-mappings-section">
          <h3>Patient ID registry (localPatientId → bdsaPatientId)</h3>
          <p className="slide-mappings-section-desc">
            Separate patient-level IDs when a center&apos;s local patient identifier differs from
            the case ID used on slides.
          </p>
          <RegistryMeta
            institutionId={patientInstitutionId}
            lastUpdated={patientLastUpdated}
            source={patientSource}
            count={filteredPatientMappings.length}
            aliasStats={[]}
          />
          {filteredPatientMappings.length === 0 ? (
            <p className="slide-mappings-empty">No patient rows match your filter.</p>
          ) : (
            <div className="slide-mappings-table-wrap">
              <table className="slide-mappings-table">
                <thead>
                  <tr>
                    <th>Local patient ID</th>
                    <th>BDSA patient ID</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredPatientMappings.map((row) => (
                    <tr key={row.localPatientId}>
                      <td>
                        <code>{row.localPatientId}</code>
                      </td>
                      <td>
                        {row.bdsaPatientId ? (
                          <code>{row.bdsaPatientId}</code>
                        ) : (
                          <span className="slide-mappings-muted">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}
    </div>
  )
}
