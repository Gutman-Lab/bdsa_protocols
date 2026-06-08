import { useMemo, useState } from 'react'
import type { CaseIdMappingItem, PatientIdMappingItem } from '../../api/idMappings'

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
}: {
  institutionId?: string
  lastUpdated?: string | null
  source?: string
  count: number
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
  caseMappings,
  caseInstitutionId,
  caseLastUpdated,
  caseSource,
  patientMappings,
  patientInstitutionId,
  patientLastUpdated,
  patientSource,
}: {
  caseMappings: CaseIdMappingItem[]
  caseInstitutionId?: string
  caseLastUpdated?: string | null
  caseSource?: string
  patientMappings: PatientIdMappingItem[]
  patientInstitutionId?: string
  patientLastUpdated?: string | null
  patientSource?: string
}) {
  const [search, setSearch] = useState('')

  const alternateSystems = useMemo(() => {
    const systems = new Set<string>()
    for (const row of caseMappings) {
      for (const key of Object.keys(row.alternateIds ?? {})) {
        systems.add(key)
      }
    }
    return [...systems].sort()
  }, [caseMappings])

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
          (e.g. <code>BDSA-002-00001</code> for U. Kentucky). Optional{' '}
          <code>alternateIds</code> crosswalk external systems (e.g. <code>nacc</code> for NACC
          case IDs linked to clinical-metadata <code>NACCID</code>).
        </p>
        <RegistryMeta
          institutionId={caseInstitutionId}
          lastUpdated={caseLastUpdated}
          source={caseSource}
          count={filteredCaseMappings.length}
        />
        {caseMappings.length === 0 ? (
          <p className="slide-mappings-empty">No case ID mappings stored for this center yet.</p>
        ) : filteredCaseMappings.length === 0 ? (
          <p className="slide-mappings-empty">No rows match your filter.</p>
        ) : (
          <div className="slide-mappings-table-wrap">
            <table className="slide-mappings-table">
              <thead>
                <tr>
                  <th>Local case ID</th>
                  <th>BDSA case ID</th>
                  {alternateSystems.map((system) => (
                    <th key={system}>{system}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filteredCaseMappings.map((row) => (
                  <tr key={`${row.localCaseId}:${row.bdsaCaseId}`}>
                    <td>
                      <code>{row.localCaseId}</code>
                    </td>
                    <td>
                      <code>{row.bdsaCaseId}</code>
                    </td>
                    {alternateSystems.map((system) => (
                      <td key={system}>
                        {row.alternateIds?.[system] ? (
                          <code>{row.alternateIds[system]}</code>
                        ) : (
                          <span className="slide-mappings-muted">—</span>
                        )}
                      </td>
                    ))}
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
