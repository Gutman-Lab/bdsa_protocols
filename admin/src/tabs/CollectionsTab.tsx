import { useEffect, useState } from 'react'
import {
  fetchCollections,
  deleteCollection,
  renameCollection,
} from '../api'
import { DataView } from '../DataView'
import './CollectionsTab.css'

interface Props {
  onCollectionsChange?: () => void
}

export function CollectionsTab({ onCollectionsChange }: Props) {
  const [data, setData] = useState<unknown>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editId, setEditId] = useState<string>('')
  const [actionError, setActionError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState(false)

  const refresh = () => {
    setLoading(true)
    setError(null)
    fetchCollections()
      .then((d) => setData(d))
      .catch((e) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false))
    onCollectionsChange?.()
  }

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    fetchCollections()
      .then((d) => {
        if (!cancelled) setData(d)
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e))
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [])

  const collectionIds = (data as { collection_ids?: string[] } | null)?.collection_ids ?? []

  const handleRename = async () => {
    if (!editId.trim()) return
    const newId = window.prompt('New collection ID:', editId)
    if (newId == null || newId.trim() === '') return
    if (newId.trim() === editId) return
    setActionError(null)
    setActionLoading(true)
    try {
      await renameCollection(editId, newId.trim())
      setEditId(newId.trim())
      refresh()
    } catch (e) {
      setActionError(e instanceof Error ? e.message : String(e))
    } finally {
      setActionLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!editId.trim()) return
    const message =
      `Are you sure you want to delete collection "${editId}"?\n\n` +
      'This will permanently delete all data for this collection: protocols, case ID mappings, patient ID mappings, slides, block→region maps, version history, and case registry.'
    if (!window.confirm(message)) return
    setActionError(null)
    setActionLoading(true)
    try {
      await deleteCollection(editId)
      setEditId('')
      refresh()
    } catch (e) {
      setActionError(e instanceof Error ? e.message : String(e))
    } finally {
      setActionLoading(false)
    }
  }

  return (
    <div className="collections-tab">
      <DataView
        title="Collections"
        data={data}
        loading={loading}
        error={error ?? undefined}
      />

      {!loading && !error && collectionIds.length > 0 && (
        <div className="collection-editor">
          <h3>Collection editor</h3>
          <p className="editor-desc">Update or delete a collection. Deletion is permanent.</p>
          <div className="editor-controls">
            <label htmlFor="edit-collection-select">Collection:</label>
            <select
              id="edit-collection-select"
              value={editId}
              onChange={(e) => {
                setEditId(e.target.value)
                setActionError(null)
              }}
            >
              <option value="">Select…</option>
              {collectionIds.map((id) => (
                <option key={id} value={id}>
                  {id}
                </option>
              ))}
            </select>
            <button
              type="button"
              className="editor-btn editor-btn-rename"
              disabled={!editId || actionLoading}
              onClick={handleRename}
            >
              Rename
            </button>
            <button
              type="button"
              className="editor-btn editor-btn-delete"
              disabled={!editId || actionLoading}
              onClick={handleDelete}
            >
              Delete
            </button>
          </div>
          {actionError && <p className="editor-error">{actionError}</p>}
        </div>
      )}
    </div>
  )
}
