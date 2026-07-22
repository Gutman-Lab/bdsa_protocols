import { useEffect, useMemo, useState } from 'react'
import { useProtocols } from 'bdsa-react-components'
import { fetchCombinedSchema, type CombinedSchemaResponse } from '../../api/schemas'
import {
  LANDMARK_APPENDIX_COLUMNS,
  REGION_FLAT_COLUMNS,
  STAIN_FLAT_COLUMNS,
  downloadTextFile,
  exportProtocolsWorkbook,
  extractLandmarkAppendix,
  flattenRegionProtocol,
  flattenStainProtocol,
  mergeColumns,
  rowsToCsv,
} from '../../utils/flattenProtocols'
import {
  analyzeRegionAbbreviations,
  analyzeStainAbbreviations,
} from '../../utils/protocolAbbreviations'
import './FlatProtocolsView.css'

function FlatTable({
  columns,
  rows,
  collidingIds,
}: {
  columns: { key: string; label: string }[]
  rows: Record<string, string>[]
  collidingIds?: Set<string>
}) {
  if (!rows.length) {
    return <p className="flat-protocols-empty">No rows.</p>
  }

  return (
    <div className="flat-protocols-table-wrap">
      <table className="flat-protocols-table">
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col.key}>{col.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => {
            const colliding = collidingIds?.has(row.id)
            return (
              <tr
                key={row.id || index}
                className={colliding ? 'flat-row-abbrev-collision' : undefined}
                title={colliding ? 'Abbreviation collides with another protocol' : undefined}
              >
                {columns.map((col) => (
                  <td
                    key={col.key}
                    title={row[col.key] ?? ''}
                    className={
                      col.key === 'abbreviation' && colliding
                        ? 'flat-cell-abbrev-collision'
                        : undefined
                    }
                  >
                    {row[col.key] ?? '—'}
                  </td>
                ))}
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

export function FlatProtocolsView({ collectionLabel }: { collectionLabel: string }) {
  const { stainProtocols, regionProtocols, loading } = useProtocols()
  const [schema, setSchema] = useState<CombinedSchemaResponse | null>(null)
  const [schemaError, setSchemaError] = useState<string | null>(null)
  const [showAppendix, setShowAppendix] = useState(false)

  useEffect(() => {
    let cancelled = false
    fetchCombinedSchema()
      .then((data) => {
        if (!cancelled) setSchema(data)
      })
      .catch((e) => {
        if (!cancelled) {
          setSchemaError(e instanceof Error ? e.message : String(e))
        }
      })
    return () => {
      cancelled = true
    }
  }, [])

  const regionRows = useMemo(
    () =>
      regionProtocols.map((p: { id?: string; [key: string]: unknown }) =>
        flattenRegionProtocol(p as Record<string, unknown>),
      ),
    [regionProtocols],
  )

  const stainRows = useMemo(
    () =>
      stainProtocols.map((p: { id?: string; [key: string]: unknown }) =>
        flattenStainProtocol(p as Record<string, unknown>),
      ),
    [stainProtocols],
  )

  const regionCollidingIds = useMemo(
    () =>
      analyzeRegionAbbreviations(
        regionProtocols as unknown as Record<string, unknown>[],
      ).collidingIds,
    [regionProtocols],
  )

  const stainCollidingIds = useMemo(
    () =>
      analyzeStainAbbreviations(
        stainProtocols as unknown as Record<string, unknown>[],
      ).collidingIds,
    [stainProtocols],
  )

  const regionColumns = useMemo(
    () => mergeColumns(REGION_FLAT_COLUMNS, regionRows),
    [regionRows],
  )

  const stainColumns = useMemo(
    () => mergeColumns(STAIN_FLAT_COLUMNS, stainRows),
    [stainRows],
  )

  const landmarkAppendix = useMemo(
    () => extractLandmarkAppendix(schema?.regionMetadata),
    [schema],
  )

  const safeSlug = collectionLabel.replace(/[^\w.-]+/g, '_').slice(0, 40) || 'export'

  const exportRegionCsv = () => {
    downloadTextFile(
      rowsToCsv(regionColumns, regionRows),
      `region-protocols-${safeSlug}.csv`,
    )
  }

  const exportStainCsv = () => {
    downloadTextFile(rowsToCsv(stainColumns, stainRows), `stain-protocols-${safeSlug}.csv`)
  }

  const exportAppendixCsv = () => {
    const rows = landmarkAppendix.map((r) => ({
      regionType: r.regionType,
      regionTitle: r.regionTitle,
      sortOrder: String(r.sortOrder),
      landmark: r.landmark,
    }))
    downloadTextFile(
      rowsToCsv(LANDMARK_APPENDIX_COLUMNS, rows),
      `landmark-reference-${safeSlug}.csv`,
    )
  }

  const exportWorkbook = () => {
    exportProtocolsWorkbook(
      collectionLabel,
      regionRows,
      stainRows,
      landmarkAppendix,
      regionColumns,
      stainColumns,
    )
  }

  if (loading) {
    return <p className="flat-protocols-loading">Loading protocols…</p>
  }

  return (
    <div className="flat-protocols-view">
      <header className="flat-protocols-header">
        <div>
          <h2>Flat QC view</h2>
          <p>
            Spreadsheet-friendly tables for reviewing region and stain protocols. Landmarks are
            split into <code>landmark_1</code>–<code>landmark_3</code>; additional landmarks appear
            in <code>landmarks_overflow</code>. The full Pitt landmark vocabulary is in the appendix
            below. Rows with colliding abbreviations are highlighted.
          </p>
        </div>
        <div className="flat-protocols-export">
          <button type="button" className="flat-export-btn" onClick={exportWorkbook}>
            Export workbook (.xls)
          </button>
          <button type="button" className="flat-export-btn flat-export-btn-secondary" onClick={exportRegionCsv}>
            Region CSV
          </button>
          <button type="button" className="flat-export-btn flat-export-btn-secondary" onClick={exportStainCsv}>
            Stain CSV
          </button>
          <button
            type="button"
            className="flat-export-btn flat-export-btn-secondary"
            onClick={exportAppendixCsv}
            disabled={!landmarkAppendix.length}
          >
            Landmark appendix CSV
          </button>
        </div>
      </header>

      <section className="flat-protocols-section">
        <h3>Region protocols ({regionRows.length})</h3>
        <FlatTable
          columns={regionColumns}
          rows={regionRows}
          collidingIds={regionCollidingIds}
        />
      </section>

      <section className="flat-protocols-section">
        <h3>Stain protocols ({stainRows.length})</h3>
        <FlatTable
          columns={stainColumns}
          rows={stainRows}
          collidingIds={stainCollidingIds}
        />
      </section>

      <section className="flat-protocols-section flat-protocols-appendix">
        <button
          type="button"
          className="flat-appendix-toggle"
          onClick={() => setShowAppendix((open) => !open)}
          aria-expanded={showAppendix}
        >
          {showAppendix ? '▾' : '▸'} Landmark reference appendix ({landmarkAppendix.length} rows)
        </button>
        {schemaError && (
          <p className="flat-protocols-schema-error">
            Could not load schema for landmark appendix: {schemaError}
          </p>
        )}
        {showAppendix && (
          <>
            <p className="flat-protocols-appendix-desc">
              Allowed landmarks per BDSA region type from the Pitt region schema — use this when
              QC&apos;ing whether survey landmarks match the controlled vocabulary.
            </p>
            <FlatTable
              columns={LANDMARK_APPENDIX_COLUMNS}
              rows={landmarkAppendix.map((r) => ({
                regionType: r.regionType,
                regionTitle: r.regionTitle,
                sortOrder: String(r.sortOrder),
                landmark: r.landmark,
              }))}
            />
          </>
        )}
      </section>
    </div>
  )
}
