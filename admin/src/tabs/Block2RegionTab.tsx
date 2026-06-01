import { useEffect, useMemo, useRef, useState } from 'react'
import { AgGridReact } from 'ag-grid-react'
import type { ColDef, SelectionChangedEvent } from 'ag-grid-community'
import {
  fetchBlock2Region,
  fetchBlock2RegionOne,
  fetchBlock2RegionStats,
  fetchBlock2RegionVersions,
  restoreBlock2RegionVersion,
  type Block2RegionCaseEntry,
  type Block2RegionVersionEntry,
} from '../api'
import { DataView } from '../DataView'
import './Block2RegionTab.css'

interface Props {
  collectionId: string | null
}

export function Block2RegionTab({ collectionId }: Props) {
  const [viewMode, setViewMode] = useState<'all' | 'one'>('one')
  const [caseIds, setCaseIds] = useState<string[]>([])
  const [selectedCaseId, setSelectedCaseId] = useState<string>('')
  const [allData, setAllData] = useState<{
    collection_id: string
    by_case: Record<string, Block2RegionCaseEntry>
  } | null>(null)
  const [oneCaseData, setOneCaseData] = useState<Block2RegionCaseEntry | null>(null)
  const [versions, setVersions] = useState<Block2RegionVersionEntry[]>([])
  const [stats, setStats] = useState<{
    casesWithMaps: number
    totalPairs: number
    validatedCount: number
    caseIds: string[]
  } | null>(null)
  const [loading, setLoading] = useState(false)
  const [loadingStats, setLoadingStats] = useState(false)
  const [loadingVersions, setLoadingVersions] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [versionsSortBy, setVersionsSortBy] = useState<'version' | 'createdAt' | 'mapping_source' | 'validated'>('version')
  const [versionsSortDir, setVersionsSortDir] = useState<'asc' | 'desc'>('desc')
  const casesGridRef = useRef<AgGridReact>(null)

  // Load stats and case list when collection changes (stats = # patients with maps)
  useEffect(() => {
    if (!collectionId) {
      setCaseIds([])
      setSelectedCaseId('')
      setStats(null)
      setAllData(null)
      setOneCaseData(null)
      setVersions([])
      setError(null)
      return
    }
    let cancelled = false
    setLoadingStats(true)
    fetchBlock2RegionStats(collectionId)
      .then((s) => {
        if (!cancelled) {
          setStats(s)
          setCaseIds(s.caseIds || [])
          setSelectedCaseId((prev) => {
            const ids = s.caseIds || []
            return ids.includes(prev) ? prev : ids[0] ?? ''
          })
        }
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e))
      })
      .finally(() => {
        if (!cancelled) setLoadingStats(false)
      })
    return () => { cancelled = true }
  }, [collectionId])

  // Load "all" data only when view mode is all
  useEffect(() => {
    if (!collectionId || viewMode !== 'all') {
      setAllData(null)
      return
    }
    let cancelled = false
    setLoading(true)
    setError(null)
    fetchBlock2Region(collectionId)
      .then((d) => {
        if (!cancelled) setAllData(d)
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e))
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [collectionId, viewMode])

  // Load single case when "one" and selected case changes
  useEffect(() => {
    if (!collectionId || viewMode !== 'one' || !selectedCaseId) {
      setOneCaseData(null)
      setVersions([])
      return
    }
    let cancelled = false
    setLoading(true)
    setError(null)
    fetchBlock2RegionOne(collectionId, selectedCaseId)
      .then((d) => {
        if (!cancelled) setOneCaseData(d.block2region ?? null)
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e))
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [collectionId, viewMode, selectedCaseId])

  // Load versions when viewing one case
  useEffect(() => {
    if (!collectionId || viewMode !== 'one' || !selectedCaseId) {
      setVersions([])
      return
    }
    let cancelled = false
    setLoadingVersions(true)
    fetchBlock2RegionVersions(collectionId, selectedCaseId)
      .then((d) => {
        if (!cancelled) setVersions(d.versions || [])
      })
      .catch(() => {
        if (!cancelled) setVersions([])
      })
      .finally(() => {
        if (!cancelled) setLoadingVersions(false)
      })
    return () => { cancelled = true }
  }, [collectionId, viewMode, selectedCaseId])

  const sortedVersions = useMemo(() => {
    const dir = versionsSortDir === 'asc' ? 1 : -1
    return [...versions].sort((a, b) => {
      if (versionsSortBy === 'version') {
        return dir * (a.version - b.version)
      }
      if (versionsSortBy === 'validated') {
        const va = a.validated ? 1 : 0
        const vb = b.validated ? 1 : 0
        return dir * (va - vb)
      }
      const sa = String(a[versionsSortBy] ?? '')
      const sb = String(b[versionsSortBy] ?? '')
      return dir * sa.localeCompare(sb, undefined, { numeric: true })
    })
  }, [versions, versionsSortBy, versionsSortDir])

  const byCase = allData?.by_case ?? {}

  /** Derive year from case_id e.g. 0S84-35 -> 1984 */
  const yearFromCaseId = (caseId: string): string => {
    const m = caseId.match(/\d{2}/)
    if (!m) return '—'
    const yy = parseInt(m[0], 10)
    const yyyy = yy >= 50 ? 1900 + yy : 2000 + yy
    return String(yyyy)
  }

  const casesRows = useMemo(() => {
    return Object.entries(byCase).map(([caseId, ent]) => ({
      case_id: caseId,
      year: yearFromCaseId(caseId),
      patient: caseId,
      gt: ent.validated ?? false,
      gtDisplay: ent.validated ? '✓' : '—',
      llm: (ent.mapping_source ?? '').toUpperCase().includes('LLM'),
      llmDisplay: (ent.mapping_source ?? '').toUpperCase().includes('LLM') ? '✓' : '—',
      pairs: Object.keys(ent.block2region ?? {}).length,
      status: ent.case_status ?? '—',
    }))
  }, [byCase])

  const casesColumnDefs = useMemo<ColDef[]>(() => [
    { field: 'year', headerName: 'Year', filter: true, sortable: true },
    { field: 'patient', headerName: 'Patient', filter: true, sortable: true },
    { field: 'gtDisplay', headerName: 'GT', filter: true, sortable: true },
    { field: 'llmDisplay', headerName: 'LLM', filter: true, sortable: true },
    { field: 'pairs', headerName: 'Pairs', filter: true, sortable: true },
    { field: 'status', headerName: 'Status', filter: true, sortable: true },
  ], [])

  const onCasesSelectionChanged = (e: SelectionChangedEvent) => {
    const row = e.api.getSelectedRows()[0] as { case_id: string } | undefined
    if (row) {
      setSelectedCaseId(row.case_id)
      setViewMode('one')
    }
  }

  const toggleVersionsSort = (col: typeof versionsSortBy) => {
    if (versionsSortBy === col) {
      setVersionsSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setVersionsSortBy(col)
      setVersionsSortDir(col === 'version' ? 'desc' : 'asc')
    }
  }

  const handleRestore = async (version: number) => {
    if (!collectionId || !selectedCaseId) return
    try {
      await restoreBlock2RegionVersion(collectionId, selectedCaseId, version)
      const d = await fetchBlock2RegionOne(collectionId, selectedCaseId)
      setOneCaseData(d.block2region ?? null)
      const v = await fetchBlock2RegionVersions(collectionId, selectedCaseId)
      setVersions(v.versions || [])
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }

  if (!collectionId) {
    return (
      <div className="tab-placeholder">
        <p>Select a collection above to view block→region maps.</p>
      </div>
    )
  }

  const displayStats = stats ?? {
    casesWithMaps: viewMode === 'all' ? Object.keys(byCase).length : 0,
    totalPairs: viewMode === 'all'
      ? Object.values(byCase).reduce((sum, ent) => sum + Object.keys(ent.block2region || {}).length, 0)
      : 0,
    validatedCount: viewMode === 'all' ? Object.values(byCase).filter((ent) => ent.validated).length : 0,
    caseIds: [],
  }

  const displayData =
    viewMode === 'one' && selectedCaseId && oneCaseData
      ? { case_id: selectedCaseId, ...oneCaseData }
      : allData

  return (
    <div className="block2region-tab">
      {/* View mode: All vs One case */}
      <div className="block2region-controls">
        <div className="view-mode">
          <label>
            <input
              type="radio"
              name="b2r-view"
              checked={viewMode === 'all'}
              onChange={() => setViewMode('all')}
            />
            All cases
          </label>
          <label>
            <input
              type="radio"
              name="b2r-view"
              checked={viewMode === 'one'}
              onChange={() => setViewMode('one')}
            />
            One case
          </label>
        </div>
        {viewMode === 'one' && (
          <select
            className="case-select"
            value={selectedCaseId}
            onChange={(e) => setSelectedCaseId(e.target.value)}
          >
            <option value="">Select case…</option>
            {caseIds.map((id) => (
              <option key={id} value={id}>
                {id}
              </option>
            ))}
          </select>
        )}
      </div>

      {collectionId && (
        <div className="block2region-stats">
          {loadingStats ? (
            <span className="stat">Loading stats…</span>
          ) : (
            <>
              <span className="stat">
                <strong>{displayStats.casesWithMaps}</strong> patient{displayStats.casesWithMaps !== 1 ? 's' : ''} with map{displayStats.casesWithMaps !== 1 ? 's' : ''}
              </span>
              <span className="stat">
                <strong>{displayStats.totalPairs}</strong> total block→region pair{displayStats.totalPairs !== 1 ? 's' : ''}
              </span>
              <span className="stat">
                <strong>{displayStats.validatedCount}</strong> validated
              </span>
            </>
          )}
        </div>
      )}

      {!loading && !error && viewMode === 'one' && caseIds.length === 0 && (
        <p className="block2region-empty">
          No cases in this collection yet. Add block→region data via the API to see cases here.
        </p>
      )}

      {!loading && !error && viewMode === 'one' && selectedCaseId && !oneCaseData && caseIds.length > 0 && (
        <p className="block2region-empty">
          This case has no block→region map yet.
        </p>
      )}

      {/* Cases table (when viewing all cases) */}
      {viewMode === 'all' && (allData != null || loading) && (
        <div className="block2region-cases-section">
          <h4>Cases</h4>
          {loading ? (
            <p className="cases-loading">Loading…</p>
          ) : casesRows.length === 0 ? (
            <p className="cases-empty">No cases with block→region data yet.</p>
          ) : (
            <div className="ag-theme-alpine cases-grid-wrap" style={{ height: 420 }}>
              <AgGridReact
                ref={casesGridRef}
                rowData={casesRows}
                columnDefs={casesColumnDefs}
                getRowId={(params) => params.data.case_id}
                rowSelection="single"
                onSelectionChanged={onCasesSelectionChanged}
                suppressRowClickSelection
                defaultColDef={{ sortable: true, filter: true, resizable: true }}
                domLayout="normal"
              />
            </div>
          )}
        </div>
      )}

      {/* Version history (only when viewing one case) */}
      {viewMode === 'one' && selectedCaseId && (
        <div className="block2region-versions">
          <h4>Version history</h4>
          {loadingVersions ? (
            <p className="versions-loading">Loading…</p>
          ) : versions.length === 0 ? (
            <p className="versions-empty">No versions yet (each PUT creates a new version).</p>
          ) : (
            <table className="versions-table">
              <thead>
                <tr>
                  <th
                    className="versions-th-sortable"
                    onClick={() => toggleVersionsSort('version')}
                    title="Sort by version"
                  >
                    Version {versionsSortBy === 'version' && (versionsSortDir === 'asc' ? ' ↑' : ' ↓')}
                  </th>
                  <th
                    className="versions-th-sortable"
                    onClick={() => toggleVersionsSort('createdAt')}
                    title="Sort by created"
                  >
                    Created {versionsSortBy === 'createdAt' && (versionsSortDir === 'asc' ? ' ↑' : ' ↓')}
                  </th>
                  <th
                    className="versions-th-sortable"
                    onClick={() => toggleVersionsSort('mapping_source')}
                    title="Sort by source"
                  >
                    Source {versionsSortBy === 'mapping_source' && (versionsSortDir === 'asc' ? ' ↑' : ' ↓')}
                  </th>
                  <th
                    className="versions-th-sortable"
                    onClick={() => toggleVersionsSort('validated')}
                    title="Sort by validated"
                  >
                    Validated {versionsSortBy === 'validated' && (versionsSortDir === 'asc' ? ' ↑' : ' ↓')}
                  </th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {sortedVersions.map((v) => (
                  <tr key={v.version}>
                    <td>{v.version}</td>
                    <td>{v.createdAt ?? '—'}</td>
                    <td>{v.mapping_source ?? '—'}</td>
                    <td>{v.validated ? 'Yes' : 'No'}</td>
                    <td>
                      <button
                        type="button"
                        className="restore-btn"
                        onClick={() => handleRestore(v.version)}
                      >
                        Restore
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      <DataView
        title={viewMode === 'one' && selectedCaseId ? `Block → region: ${selectedCaseId}` : 'Block → region (by case)'}
        data={displayData}
        loading={loading}
        error={error ?? undefined}
      />
    </div>
  )
}
