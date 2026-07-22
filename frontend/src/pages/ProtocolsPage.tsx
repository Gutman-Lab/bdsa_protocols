import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  ProtocolProvider,
  ProtocolsTab,
  createSchemaValidator,
} from 'bdsa-react-components'
import {
  fetchCollections,
  updateCollectionDisplayName,
} from '../api/protocols'
import { getApiUrl } from '../api/client'
import { ApiProtocolStorage } from '../protocols/apiProtocolStorage'
import {
  formatCollectionLabel,
  findCollection,
  suggestNewCollectionId,
  type CollectionSummary,
} from '../utils/collectionLabels'
import { fetchCombinedSchema } from '../api/schemas'
import { BlockProtocolsPanel } from '../components/protocols/BlockProtocolsPanel'
import { FlatProtocolsView } from '../components/protocols/FlatProtocolsView'
import { AbbreviationCollisionBanner } from '../components/protocols/AbbreviationCollisionBanner'
import './ProtocolsPage.css'

type ProtocolsViewMode = 'edit' | 'block' | 'flat'

export default function ProtocolsPage() {
  const schemaValidator = useMemo(() => createSchemaValidator(), [])
  const [schemaReady, setSchemaReady] = useState(false)
  const [schemaError, setSchemaError] = useState<string | null>(null)
  const [collections, setCollections] = useState<CollectionSummary[]>([])
  const [collectionsLoading, setCollectionsLoading] = useState(true)
  const [collectionsError, setCollectionsError] = useState<string | null>(null)
  const [collectionId, setCollectionId] = useState(
    () => (import.meta.env.VITE_DEFAULT_COLLECTION_ID || '').trim(),
  )
  const [newCollectionName, setNewCollectionName] = useState('')
  const [advancedId, setAdvancedId] = useState('')
  const [showAdvancedId, setShowAdvancedId] = useState(false)
  const [viewMode, setViewMode] = useState<ProtocolsViewMode>('edit')

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
      if (!collectionId) {
        setCollectionId(items[0].collection_id)
      }
    })
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- seed default once
  }, [loadCollections])

  useEffect(() => {
    let cancelled = false
    setSchemaReady(false)
    setSchemaError(null)
    fetchCombinedSchema()
      .then((combined) => schemaValidator.loadSchemas(undefined, combined))
      .then(() => {
        if (!cancelled) setSchemaReady(true)
      })
      .catch((e) => {
        if (!cancelled) {
          setSchemaError(e instanceof Error ? e.message : String(e))
          setSchemaReady(true)
        }
      })
    return () => {
      cancelled = true
    }
  }, [schemaValidator])

  const storage = useMemo(
    () => new ApiProtocolStorage(collectionId),
    [collectionId],
  )

  const activeId = collectionId.trim()
  const selected = findCollection(collections, activeId)

  const handleRenameSelected = async () => {
    if (!activeId) return
    const current = selected?.display_name ?? ''
    const name = window.prompt('Collection display name:', current)
    if (name == null || !name.trim() || name.trim() === current) return
    try {
      await updateCollectionDisplayName(activeId, name.trim())
      await loadCollections()
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e))
    }
  }

  const handleAddCollection = async () => {
    const name = newCollectionName.trim()
    if (!name) return
    const id = suggestNewCollectionId(collections)
    try {
      await updateCollectionDisplayName(id, name)
      await loadCollections()
      setCollectionId(id)
      setNewCollectionName('')
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e))
    }
  }

  const handleUseAdvancedId = async () => {
    const id = advancedId.trim()
    if (!id) return
    const existing = findCollection(collections, id)
    if (!existing) {
      const name = window.prompt('Display name for this collection:', `Collection ${collections.length + 1}`)
      if (name == null || !name.trim()) return
      try {
        await updateCollectionDisplayName(id, name.trim())
        await loadCollections()
      } catch (e) {
        alert(e instanceof Error ? e.message : String(e))
        return
      }
    }
    setCollectionId(id)
    setAdvancedId('')
  }

  return (
    <div className="protocols-page">
      <div className="protocols-toolbar">
        <div className="protocols-toolbar-main">
          <label className="protocols-collection-label" htmlFor="protocols-collection-select">
            Collection
          </label>
          <select
            id="protocols-collection-select"
            className="protocols-collection-select"
            value={activeId}
            onChange={(e) => setCollectionId(e.target.value)}
            disabled={collectionsLoading}
          >
            <option value="">Select a collection…</option>
            {collections.map((c) => (
              <option key={c.collection_id} value={c.collection_id}>
                {formatCollectionLabel(c)}
              </option>
            ))}
            {activeId && !collections.some((c) => c.collection_id === activeId) && (
              <option value={activeId}>
                {selected ? formatCollectionLabel(selected) : activeId}
              </option>
            )}
          </select>
          <button
            type="button"
            className="protocols-rename-btn"
            disabled={!activeId}
            onClick={handleRenameSelected}
            title="Rename selected collection"
          >
            Rename
          </button>
          <div className="protocols-new-collection">
            <input
              type="text"
              placeholder="New collection name"
              value={newCollectionName}
              onChange={(e) => setNewCollectionName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') void handleAddCollection()
              }}
            />
            <button
              type="button"
              className="protocols-use-id-btn"
              disabled={!newCollectionName.trim()}
              onClick={() => void handleAddCollection()}
            >
              Add
            </button>
          </div>
        </div>
        <div className="protocols-toolbar-meta">
          <div className="protocols-toolbar-meta-line">
            {selected && (
              <span className="protocols-meta-item protocols-collection-id-hint">
                ID <code>{selected.collection_id}</code> (API; #{selected.number} auto)
              </span>
            )}
            <button
              type="button"
              className="protocols-meta-item protocols-meta-link"
              onClick={() => setShowAdvancedId((open) => !open)}
              aria-expanded={showAdvancedId}
            >
              {showAdvancedId ? '▾' : '▸'} Use an existing collection ID
            </button>
            <span className="protocols-meta-item protocols-api-hint">
              API: {getApiUrl() || '(same origin /api proxy)'}
              {collectionsError && (
                <span className="protocols-collections-error"> — {collectionsError}</span>
              )}
            </span>
          </div>
          {showAdvancedId && (
            <div className="protocols-advanced-id-row">
              <input
                type="text"
                placeholder="Collection ID (e.g. Girder folder id)"
                value={advancedId}
                onChange={(e) => setAdvancedId(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') void handleUseAdvancedId()
                }}
              />
              <button
                type="button"
                className="protocols-use-id-btn"
                disabled={!advancedId.trim()}
                onClick={() => void handleUseAdvancedId()}
              >
                Use ID
              </button>
            </div>
          )}
        </div>
      </div>

      {!activeId ? (
        <p className="protocols-pick-collection">
          Choose a collection to load and edit stain and region protocols, or add a new named
          collection above.
        </p>
      ) : (
        <ProtocolProvider key={activeId} storage={storage}>
          <AbbreviationCollisionBanner />
          <div className="protocols-view-tabs" role="tablist" aria-label="Protocol views">
            <button
              type="button"
              role="tab"
              aria-selected={viewMode === 'edit'}
              className={`protocols-view-tab${viewMode === 'edit' ? ' active' : ''}`}
              onClick={() => setViewMode('edit')}
            >
              Edit protocols
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={viewMode === 'block'}
              className={`protocols-view-tab${viewMode === 'block' ? ' active' : ''}`}
              onClick={() => setViewMode('block')}
            >
              Block protocols
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={viewMode === 'flat'}
              className={`protocols-view-tab${viewMode === 'flat' ? ' active' : ''}`}
              onClick={() => setViewMode('flat')}
            >
              Flat QC export
            </button>
          </div>
          {viewMode === 'flat' ? (
            <FlatProtocolsView
              collectionLabel={
                selected ? formatCollectionLabel(selected) : activeId
              }
            />
          ) : viewMode === 'block' ? (
            <BlockProtocolsPanel
              collectionId={activeId}
              collectionLabel={selected ? formatCollectionLabel(selected) : activeId}
            />
          ) : !schemaReady ? (
            <p className="protocols-pick-collection">Loading BDSA schema for form options…</p>
          ) : (
            <>
              {schemaError && (
                <p className="protocols-collections-error">
                  Schema load failed ({schemaError}) — using fallback dropdown options.
                </p>
              )}
              <ProtocolsTab
                schemaValidator={schemaValidator}
                title="Stain and region protocols"
                description={
                  selected
                    ? `${formatCollectionLabel(selected)} — stain and region protocols (saved to the API).`
                    : `Protocols for collection ${activeId}.`
                }
              />
            </>
          )}
        </ProtocolProvider>
      )}
    </div>
  )
}
