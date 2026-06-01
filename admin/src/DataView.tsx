import { useMemo, useState } from 'react'
import { AgGridReact } from 'ag-grid-react'
import type { ColDef } from 'ag-grid-community'
import './DataView.css'

type ViewMode = 'json' | 'table'

interface DataViewProps {
  title: string
  data: unknown
  loading?: boolean
  error?: string
  tableColumns?: string[] // for table view; if not set we try to infer from first row
}

export function DataView({ title, data, loading, error, tableColumns }: DataViewProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('json')

  // Hooks must run before any early return (React #310)
  const json = JSON.stringify(data ?? null, null, 2)
  const rows: Record<string, unknown>[] = Array.isArray(data)
    ? data.filter((x): x is Record<string, unknown> => typeof x === 'object' && x !== null)
    : data && typeof data === 'object' && 'by_case' in data
      ? Object.entries((data as { by_case: Record<string, Record<string, string>> }).by_case).map(
          ([caseId, blockMap]) => ({ case_id: caseId, ...blockMap })
        )
      : data && typeof data === 'object' && data !== null
        ? [data as Record<string, unknown>]
        : []

  const cols = tableColumns?.length
    ? tableColumns
    : rows.length
      ? Array.from(new Set(rows.flatMap((r) => Object.keys(r))))
      : []

  const columnDefs = useMemo<ColDef[]>(
    () =>
      cols.map((field) => ({
        field,
        headerName: field,
        filter: true,
        sortable: true,
        resizable: true,
        valueFormatter: (params: { value: unknown }) => {
          const v = params.value
          if (v != null && typeof v === 'object') return JSON.stringify(v)
          return v != null ? String(v) : ''
        },
      })),
    [cols]
  )

  if (loading) {
    return (
      <div className="data-view">
        <h3>{title}</h3>
        <p className="data-view-loading">Loading…</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="data-view">
        <h3>{title}</h3>
        <p className="data-view-error">{error}</p>
      </div>
    )
  }

  return (
    <div className="data-view">
      <div className="data-view-header">
        <h3>{title}</h3>
        <div className="data-view-toggles">
          <button
            type="button"
            className={viewMode === 'json' ? 'active' : ''}
            onClick={() => setViewMode('json')}
          >
            JSON
          </button>
          <button
            type="button"
            className={viewMode === 'table' ? 'active' : ''}
            onClick={() => setViewMode('table')}
          >
            Table
          </button>
        </div>
      </div>
      {viewMode === 'json' && (
        <pre className="data-view-json">{json}</pre>
      )}
      {viewMode === 'table' && (
        <div className="ag-theme-alpine data-view-grid-wrap">
          <AgGridReact
            rowData={rows}
            columnDefs={columnDefs}
            defaultColDef={{ sortable: true, filter: true, resizable: true }}
            domLayout="normal"
          />
        </div>
      )}
    </div>
  )
}
