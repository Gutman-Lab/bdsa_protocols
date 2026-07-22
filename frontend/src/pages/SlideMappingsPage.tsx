import { useCallback, useEffect, useMemo, useState } from 'react'
import { fetchCollections } from '../api/protocols'
import {
  fetchSlideMappingBundle,
  type RegionLabelMappingItem,
  type StainLabelMappingItem,
} from '../api/slideMappings'
import { CaseIdMappingsTab } from '../components/slideMappings/CaseIdMappingsTab'
import { ProtocolDefinitionsTab } from '../components/slideMappings/ProtocolDefinitionsTab'
import { ProtocolHoverPanel } from '../components/slideMappings/ProtocolHoverPanel'
import {
  findCollection,
  formatCollectionLabel,
  type CollectionSummary,
} from '../utils/collectionLabels'
import {
  REGION_SUMMARY_KEYS,
  STAIN_SUMMARY_KEYS,
  protocolField,
} from '../utils/protocolDisplay'
import { findProtocolById, protocolRowHoverHandlers } from '../utils/protocolHover'
import {
  formatBlockSlotsSummary,
  normalizeBlockProtocol,
} from '../utils/blockProtocols'
import './SlideMappingsPage.css'

type MappingTab = 'stain' | 'block' | 'cases' | 'protocols'

const PREFERRED_COLLECTION = 'kentucky'

function protocolName(
  protocols: Record<string, unknown>[],
  id: string,
): string {
  const match = protocols.find((p) => p.id === id)
  return (match?.name as string) || '—'
}

function ValidatedBadge({ validated }: { validated?: boolean }) {
  return validated !== false ? (
    <span className="slide-mappings-badge ok">validated</span>
  ) : (
    <span className="slide-mappings-badge pending">review</span>
  )
}

function StainTab({
  stainProtocols,
  mappings,
  highlightedProtocolId,
  onProtocolHover,
}: {
  stainProtocols: Record<string, unknown>[]
  mappings: StainLabelMappingItem[]
  highlightedProtocolId: string | null
  onProtocolHover: (id: string | null) => void
}) {
  return (
    <div>
      <section className="slide-mappings-section">
        <h3>Numeric STAIN codes (1–{stainProtocols.length})</h3>
        <p className="slide-mappings-section-desc">
          Survey block stain indices map to protocols in list order (STAIN 1 → first stain protocol).
        </p>
        {stainProtocols.length === 0 ? (
          <p className="slide-mappings-empty">No stain protocols defined for this center.</p>
        ) : (
          <div className="slide-mappings-table-wrap">
            <table className="slide-mappings-table">
              <thead>
                <tr>
                  <th>STAIN code</th>
                  <th>Protocol</th>
                  <th>Protocol name</th>
                  {STAIN_SUMMARY_KEYS.map((col) => (
                    <th key={col.key}>{col.label}</th>
                  ))}
                  <th>Source field</th>
                </tr>
              </thead>
              <tbody>
                {stainProtocols.map((protocol, index) => (
                  <tr
                    key={String(protocol.id)}
                    {...protocolRowHoverHandlers(
                      String(protocol.id),
                      highlightedProtocolId,
                      onProtocolHover,
                    )}
                  >
                    <td>{index + 1}</td>
                    <td>
                      <code>{String(protocol.id)}</code>
                    </td>
                    <td>{String(protocol.name ?? '—')}</td>
                    {STAIN_SUMMARY_KEYS.map((col) => (
                      <td key={col.key}>{protocolField(protocol, col.key)}</td>
                    ))}
                    <td>
                      <span className="slide-mappings-badge field">STAIN</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="slide-mappings-section">
        <h3>STAINO free-text mappings</h3>
        <p className="slide-mappings-section-desc">
          Overrides and aliases from the stain-label-mappings registry ({mappings.length} rows).
        </p>
        {mappings.length === 0 ? (
          <p className="slide-mappings-empty">No STAINO label mappings stored yet.</p>
        ) : (
          <div className="slide-mappings-table-wrap">
            <table className="slide-mappings-table">
              <thead>
                <tr>
                  <th>Label</th>
                  <th>Normalized</th>
                  <th>Protocol</th>
                  <th>Protocol name</th>
                  <th>Field</th>
                  <th>Status</th>
                  <th>Source</th>
                </tr>
              </thead>
              <tbody>
                {mappings.map((row) => (
                  <tr
                    key={row.normalized ?? row.stainLabel}
                    {...protocolRowHoverHandlers(
                      row.stainProtocolId,
                      highlightedProtocolId,
                      onProtocolHover,
                    )}
                  >
                    <td>{row.stainLabel}</td>
                    <td>
                      <code>{row.normalized}</code>
                    </td>
                    <td>
                      <code>{row.stainProtocolId}</code>
                    </td>
                    <td>{protocolName(stainProtocols, row.stainProtocolId)}</td>
                    <td>
                      <span className="slide-mappings-badge field">
                        {row.sourceField ?? 'STAINO'}
                      </span>
                    </td>
                    <td>
                      <ValidatedBadge validated={row.validated} />
                    </td>
                    <td>{row.source ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}

function BlockTab({
  regionProtocols,
  blockProtocols,
  mappings,
  highlightedProtocolId,
  onProtocolHover,
}: {
  regionProtocols: Record<string, unknown>[]
  blockProtocols: Record<string, unknown>[]
  mappings: RegionLabelMappingItem[]
  highlightedProtocolId: string | null
  onProtocolHover: (id: string | null) => void
}) {
  const explicitBlocks = blockProtocols.length > 0
  const normalizedBlocks = useMemo(
    () => blockProtocols.map((b) => normalizeBlockProtocol(b)),
    [blockProtocols],
  )

  return (
    <div>
      <section className="slide-mappings-section">
        <h3>
          {explicitBlocks
            ? 'Block protocols'
            : `Survey block indices (REGION 1–${regionProtocols.length})`}
        </h3>
        <p className="slide-mappings-section-desc">
          {explicitBlocks
            ? 'Collection-level blocking protocols — each block may include multiple region protocols.'
            : 'When REGION is numeric (1–14), block index maps to region protocols in list order.'}
        </p>
        {explicitBlocks ? (
          <div className="slide-mappings-table-wrap">
            <table className="slide-mappings-table">
              <thead>
                <tr>
                  <th>Block ID</th>
                  <th>Name</th>
                  <th>Region protocols in block</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                {normalizedBlocks.map((block) => (
                  <tr key={block.id}>
                    <td>
                      <code>{block.id}</code>
                    </td>
                    <td>{block.name}</td>
                    <td>{formatBlockSlotsSummary(block, regionProtocols)}</td>
                    <td>{block.description || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : regionProtocols.length === 0 ? (
          <p className="slide-mappings-empty">No region protocols defined for this center.</p>
        ) : (
          <div className="slide-mappings-table-wrap">
            <table className="slide-mappings-table">
              <thead>
                <tr>
                  <th>Block / REGION</th>
                  <th>Region protocol</th>
                  <th>Protocol name</th>
                  {REGION_SUMMARY_KEYS.map((col) => (
                    <th key={col.key}>{col.label}</th>
                  ))}
                  <th>Source field</th>
                </tr>
              </thead>
              <tbody>
                {regionProtocols.map((protocol, index) => (
                  <tr
                    key={String(protocol.id)}
                    {...protocolRowHoverHandlers(
                      String(protocol.id),
                      highlightedProtocolId,
                      onProtocolHover,
                    )}
                  >
                    <td>{index + 1}</td>
                    <td>
                      <code>{String(protocol.id)}</code>
                    </td>
                    <td>{String(protocol.name ?? '—')}</td>
                    {REGION_SUMMARY_KEYS.map((col) => (
                      <td key={col.key}>{protocolField(protocol, col.key)}</td>
                    ))}
                    <td>
                      <span className="slide-mappings-badge field">REGION</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="slide-mappings-section">
        <h3>REGIONO / free-text region mappings</h3>
        <p className="slide-mappings-section-desc">
          Label crosswalk from region-label-mappings ({mappings.length} rows). Used when REGIONO
          (or other free text) appears on slides.
        </p>
        {mappings.length === 0 ? (
          <p className="slide-mappings-empty">No region label mappings stored yet.</p>
        ) : (
          <div className="slide-mappings-table-wrap">
            <table className="slide-mappings-table">
              <thead>
                <tr>
                  <th>Label</th>
                  <th>Normalized</th>
                  <th>Region protocol</th>
                  <th>Protocol name</th>
                  <th>Field</th>
                  <th>Status</th>
                  <th>Source</th>
                </tr>
              </thead>
              <tbody>
                {mappings.map((row) => (
                  <tr
                    key={row.normalized ?? row.regionLabel}
                    {...protocolRowHoverHandlers(
                      row.regionProtocolId,
                      highlightedProtocolId,
                      onProtocolHover,
                    )}
                  >
                    <td>{row.regionLabel}</td>
                    <td>
                      <code>{row.normalized}</code>
                    </td>
                    <td>
                      <code>{row.regionProtocolId}</code>
                    </td>
                    <td>{protocolName(regionProtocols, row.regionProtocolId)}</td>
                    <td>
                      <span className="slide-mappings-badge field">
                        {row.sourceField ?? 'REGIONO'}
                      </span>
                    </td>
                    <td>
                      <ValidatedBadge validated={row.validated} />
                    </td>
                    <td>{row.source ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}

export default function SlideMappingsPage() {
  const [collections, setCollections] = useState<CollectionSummary[]>([])
  const [collectionsLoading, setCollectionsLoading] = useState(true)
  const [collectionsError, setCollectionsError] = useState<string | null>(null)
  const [collectionId, setCollectionId] = useState('')
  const [activeTab, setActiveTab] = useState<MappingTab>('stain')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [bundle, setBundle] = useState<Awaited<ReturnType<typeof fetchSlideMappingBundle>> | null>(
    null,
  )
  const [hoveredProtocolId, setHoveredProtocolId] = useState<string | null>(null)

  const loadCollections = useCallback(() => {
    setCollectionsLoading(true)
    setCollectionsError(null)
    return fetchCollections()
      .then((res) => {
        const items =
          res.collections ??
          (res.collection_ids ?? []).map((id, i) => ({
            collection_id: id,
            display_name: `Collection ${i + 1}`,
            number: i + 1,
          }))
        setCollections(items)
        return items
      })
      .catch((e) => {
        const msg = e instanceof Error ? e.message : String(e)
        setCollectionsError(msg)
        return [] as CollectionSummary[]
      })
      .finally(() => setCollectionsLoading(false))
  }, [])

  useEffect(() => {
    let cancelled = false
    loadCollections().then((items) => {
      if (cancelled || !items.length) return
      const preferred = items.find((c) => c.collection_id === PREFERRED_COLLECTION)
      setCollectionId((current) => current || preferred?.collection_id || items[0].collection_id)
    })
    return () => {
      cancelled = true
    }
  }, [loadCollections])

  const refreshBundle = useCallback(() => {
    if (!collectionId) return
    fetchSlideMappingBundle(collectionId)
      .then((data) => setBundle(data))
      .catch((e) => setError(e instanceof Error ? e.message : String(e)))
  }, [collectionId])

  useEffect(() => {
    if (!collectionId) {
      setBundle(null)
      return
    }
    let cancelled = false
    setLoading(true)
    setError(null)
    fetchSlideMappingBundle(collectionId)
      .then((data) => {
        if (!cancelled) setBundle(data)
      })
      .catch((e) => {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : String(e))
          setBundle(null)
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [collectionId])

  useEffect(() => {
    setHoveredProtocolId(null)
  }, [activeTab, collectionId])

  const selected = useMemo(
    () => findCollection(collections, collectionId),
    [collections, collectionId],
  )

  const stainProtocols = bundle?.protocols.stainProtocols ?? []
  const regionProtocols = bundle?.protocols.regionProtocols ?? []
  const blockProtocols = bundle?.protocols.blockProtocols ?? []

  const hoveredProtocol = useMemo(
    () => findProtocolById(stainProtocols, regionProtocols, hoveredProtocolId),
    [stainProtocols, regionProtocols, hoveredProtocolId],
  )

  const showHoverPanel = activeTab === 'stain' || activeTab === 'block'

  return (
    <div className="slide-mappings-page">
      <div className="slide-mappings-intro">
        <h2>Slide → protocol mappings</h2>
        <p>
          How slide-level CSV fields (STAIN, STAINO, REGION, REGIONO) resolve to stain and region
          protocols, and how local case/patient IDs map to canonical BDSA case IDs.{' '}
          <strong>Hover any row</strong> on Stain or Block tabs to preview protocol details in the
          side panel.
        </p>
      </div>

      <div className="slide-mappings-toolbar">
        <label htmlFor="slide-mappings-center">Center</label>
        <select
          id="slide-mappings-center"
          className="slide-mappings-select"
          value={collectionId}
          onChange={(e) => setCollectionId(e.target.value)}
          disabled={collectionsLoading}
        >
          <option value="">Select a center…</option>
          {collections.map((c) => (
            <option key={c.collection_id} value={c.collection_id}>
              {formatCollectionLabel(c)}
            </option>
          ))}
        </select>
        {selected && (
          <span className="slide-mappings-meta">
            API id <code>{selected.collection_id}</code>
          </span>
        )}
        {collectionsError && (
          <span className="slide-mappings-error">{collectionsError}</span>
        )}
      </div>

      {!collectionId ? (
        <p className="slide-mappings-empty">Select a center to view mappings.</p>
      ) : (
        <>
          <div className="slide-mappings-nav">
            <button
              type="button"
              className={`slide-mappings-nav-btn ${activeTab === 'stain' ? 'active' : ''}`}
              onClick={() => setActiveTab('stain')}
            >
              Stain
            </button>
            <button
              type="button"
              className={`slide-mappings-nav-btn ${activeTab === 'block' ? 'active' : ''}`}
              onClick={() => setActiveTab('block')}
            >
              Block / region
            </button>
            <button
              type="button"
              className={`slide-mappings-nav-btn ${activeTab === 'cases' ? 'active' : ''}`}
              onClick={() => setActiveTab('cases')}
            >
              Case IDs
              {bundle && bundle.caseMappings.length > 0 && (
                <span className="slide-mappings-nav-count">{bundle.caseMappings.length}</span>
              )}
            </button>
            <button
              type="button"
              className={`slide-mappings-nav-btn ${activeTab === 'protocols' ? 'active' : ''}`}
              onClick={() => setActiveTab('protocols')}
            >
              Protocol details
            </button>
          </div>

          <div className="slide-mappings-content">
            {loading && <p className="slide-mappings-loading">Loading mappings…</p>}
            {error && <p className="slide-mappings-error">Error: {error}</p>}
            {!loading && !error && bundle && (
              <div className={showHoverPanel ? 'slide-mappings-split' : undefined}>
                <div className={showHoverPanel ? 'slide-mappings-split-main' : undefined}>
                  {activeTab === 'stain' && (
                    <StainTab
                      stainProtocols={stainProtocols}
                      mappings={bundle.stainLabelMappings}
                      highlightedProtocolId={hoveredProtocolId}
                      onProtocolHover={setHoveredProtocolId}
                    />
                  )}
                  {activeTab === 'block' && (
                    <BlockTab
                      regionProtocols={regionProtocols}
                      blockProtocols={blockProtocols}
                      mappings={bundle.regionLabelMappings}
                      highlightedProtocolId={hoveredProtocolId}
                      onProtocolHover={setHoveredProtocolId}
                    />
                  )}
                  {activeTab === 'cases' && (
                    <CaseIdMappingsTab
                      collectionId={collectionId}
                      caseMappings={bundle.caseMappings}
                      caseInstitutionId={bundle.caseInstitutionId}
                      caseLastUpdated={bundle.caseLastUpdated}
                      caseSource={bundle.caseSource}
                      patientMappings={bundle.patientMappings}
                      patientInstitutionId={bundle.patientInstitutionId}
                      patientLastUpdated={bundle.patientLastUpdated}
                      patientSource={bundle.patientSource}
                      onMappingsUpdated={refreshBundle}
                    />
                  )}
                  {activeTab === 'protocols' && (
                    <ProtocolDefinitionsTab
                      stainProtocols={stainProtocols}
                      regionProtocols={regionProtocols}
                      hoveredProtocolId={hoveredProtocolId}
                      onProtocolHover={setHoveredProtocolId}
                    />
                  )}
                </div>
                {showHoverPanel && (
                  <ProtocolHoverPanel
                    protocol={hoveredProtocol?.protocol ?? null}
                    variant={hoveredProtocol?.variant ?? (activeTab === 'stain' ? 'stain' : 'region')}
                  />
                )}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
