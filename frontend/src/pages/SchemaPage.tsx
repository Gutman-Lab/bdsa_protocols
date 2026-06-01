/**
 * BDSA schema viewer — Pitt split schemas (pitt-bdsa/bdsa girder_bdsa/schemas)
 */
import { useEffect, useState } from 'react'
import SchemaViewer from '../components/schema/SchemaViewer'
import FlattenedDataView from '../components/schema/FlattenedDataView'
import CdeReferenceView from '../components/schema/CdeReferenceView'
import { SCHEMA_PATHS, loadAllSchemas } from '../utils/schemaLoader'
import './SchemaPage.css'

type SchemaTabId =
  | 'clinical'
  | 'region'
  | 'stain'
  | 'slide'
  | 'flattened'
  | 'cde-reference'

const SCHEMA_TABS: { id: SchemaTabId; label: string; file?: string }[] = [
  { id: 'clinical', label: 'Clinical', file: SCHEMA_PATHS.clinical },
  { id: 'region', label: 'Region', file: SCHEMA_PATHS.region },
  { id: 'stain', label: 'Stain', file: SCHEMA_PATHS.stain },
  { id: 'slide', label: 'Slide level', file: SCHEMA_PATHS.slide },
  { id: 'flattened', label: 'Flattened view' },
  { id: 'cde-reference', label: 'CDE reference' },
]

export default function SchemaPage() {
  const [activeSchema, setActiveSchema] = useState<SchemaTabId>('clinical')
  const [combinedSchema, setCombinedSchema] = useState<Record<string, unknown> | null>(null)
  const [combinedError, setCombinedError] = useState<string | null>(null)
  const [combinedLoading, setCombinedLoading] = useState(false)

  const active = SCHEMA_TABS.find((s) => s.id === activeSchema)
  const needsCombined = activeSchema === 'flattened' || activeSchema === 'cde-reference'

  useEffect(() => {
    if (!needsCombined) return
    let cancelled = false
    setCombinedLoading(true)
    setCombinedError(null)
    loadAllSchemas()
      .then(({ combined }) => {
        if (!cancelled) setCombinedSchema(combined)
      })
      .catch((e) => {
        if (!cancelled) {
          setCombinedError(e instanceof Error ? e.message : String(e))
        }
      })
      .finally(() => {
        if (!cancelled) setCombinedLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [needsCombined, activeSchema])

  return (
    <div className="schema-page">
      <div className="schema-page-intro">
        <h2>BDSA Schema</h2>
        <p>
          Pitt BDSA split JSON schemas (clinical, region, stain, slide-level). Source:{' '}
          <a
            href="https://github.com/pitt-bdsa/bdsa/tree/main/girder-plugins/girder-bdsa/girder_bdsa/schemas"
            target="_blank"
            rel="noreferrer"
          >
            pitt-bdsa/bdsa
          </a>
          .
        </p>
      </div>

      <div className="schema-navigation">
        {SCHEMA_TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={`schema-nav-button ${activeSchema === tab.id ? 'active' : ''}`}
            onClick={() => setActiveSchema(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="schema-content">
        {activeSchema === 'flattened' ? (
          combinedLoading ? (
            <p className="schema-loading">Loading schemas…</p>
          ) : combinedError ? (
            <p className="schema-error">Error: {combinedError}</p>
          ) : (
            <FlattenedDataView schemaFile={undefined} schemaData={combinedSchema} />
          )
        ) : activeSchema === 'cde-reference' ? (
          combinedLoading ? (
            <p className="schema-loading">Loading schemas…</p>
          ) : combinedError ? (
            <p className="schema-error">Error: {combinedError}</p>
          ) : (
            <CdeReferenceView schemaFile={undefined} schemaData={combinedSchema} />
          )
        ) : (
          <SchemaViewer
            schemaFile={active?.file}
            schemaData={undefined}
            schemaSection={undefined}
            schemaType={active?.label ?? 'Schema'}
          />
        )}
      </div>
    </div>
  )
}
