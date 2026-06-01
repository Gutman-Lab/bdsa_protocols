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
import './ProtocolsPage.css'

export default function ProtocolsPage() {
  const schemaValidator = useMemo(() => createSchemaValidator(), [])
  const [collections, setCollections] = useState<CollectionSummary[]>([])
  const [collectionsLoading, setCollectionsLoading] = useState(true)
  const [collectionsError, setCollectionsError] = useState<string | null>(null)
  const [collectionId, setCollectionId] = useState(
    () => (import.meta.env.VITE_DEFAULT_COLLECTION_ID || '').trim(),
  )
  const [newCollectionName, setNewCollectionName] = useState('')
  const [advancedId, setAdvancedId] = useState('')

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
        {selected && (
          <p className="protocols-collection-id-hint">
            ID <code>{selected.collection_id}</code> (used by the API; #{selected.number} assigned
            automatically)
          </p>
        )}
        <details className="protocols-advanced-id">
          <summary>Use an existing collection ID</summary>
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
        </details>
        <p className="protocols-api-hint">
          API: {getApiUrl() || '(same origin /api proxy)'}
          {collectionsError && (
            <span className="protocols-collections-error"> — {collectionsError}</span>
          )}
        </p>
      </div>

      {!activeId ? (
        <p className="protocols-pick-collection">
          Choose a collection to load and edit stain and region protocols, or add a new named
          collection above.
        </p>
      ) : (
        <ProtocolProvider key={activeId} storage={storage}>
          <ProtocolsTab
            schemaValidator={schemaValidator}
            useBundledBdsaSchema
            title="Stain and region protocols"
            description={
              selected
                ? `${formatCollectionLabel(selected)} — stain and region protocols (saved to the API).`
                : `Protocols for collection ${activeId}.`
            }
          />
        </ProtocolProvider>
      )}
    </div>
  )
}
