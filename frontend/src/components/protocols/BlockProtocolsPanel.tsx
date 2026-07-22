import { useCallback, useEffect, useMemo, useState } from 'react'
import { hasApiKey } from '../../api/client'
import { fetchCollectionProtocols, putCollectionProtocols } from '../../api/protocols'
import {
  blockProtocolToPayload,
  formatBlockSlotsSummary,
  normalizeBlockProtocol,
  type BlockProtocol,
} from '../../utils/blockProtocols'
import { analyzeBlockSlotAbbreviationCollisions } from '../../utils/protocolAbbreviations'
import { BlockProtocolModal } from './BlockProtocolModal'
import './BlockProtocolsPanel.css'

export function BlockProtocolsPanel({
  collectionId,
  collectionLabel,
}: {
  collectionId: string
  collectionLabel: string
}) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [regionProtocols, setRegionProtocols] = useState<Record<string, unknown>[]>([])
  const [blockProtocols, setBlockProtocols] = useState<BlockProtocol[]>([])
  const [fullPayload, setFullPayload] = useState<{
    stainProtocols: Record<string, unknown>[]
    regionProtocols: Record<string, unknown>[]
    source?: string
    version?: string
  } | null>(null)
  const [editing, setEditing] = useState<BlockProtocol | null | 'new'>(null)
  const canEdit = hasApiKey()

  const load = useCallback(() => {
    setLoading(true)
    setError(null)
    return fetchCollectionProtocols(collectionId)
      .then((res) => {
        const payload = res.protocols
        setFullPayload({
          stainProtocols: payload.stainProtocols ?? [],
          regionProtocols: payload.regionProtocols ?? [],
          source: payload.source,
          version: payload.version,
        })
        setRegionProtocols(payload.regionProtocols ?? [])
        setBlockProtocols(
          (payload.blockProtocols ?? []).map((row) =>
            normalizeBlockProtocol(row as Record<string, unknown>),
          ),
        )
      })
      .catch((e) => {
        setError(e instanceof Error ? e.message : String(e))
      })
      .finally(() => setLoading(false))
  }, [collectionId])

  useEffect(() => {
    void load()
  }, [load])

  const collectionPrefix = useMemo(
    () => collectionId.replace(/[^a-z0-9]+/gi, '_').toLowerCase() || 'collection',
    [collectionId],
  )

  const existingIds = useMemo(() => blockProtocols.map((b) => b.id), [blockProtocols])

  const slotCollision = useMemo(
    () => analyzeBlockSlotAbbreviationCollisions(blockProtocols, regionProtocols),
    [blockProtocols, regionProtocols],
  )

  const persistBlocks = async (nextBlocks: BlockProtocol[]) => {
    if (!fullPayload) throw new Error('Protocols not loaded')
    await putCollectionProtocols(collectionId, {
      stainProtocols: fullPayload.stainProtocols,
      regionProtocols: fullPayload.regionProtocols,
      blockProtocols: nextBlocks.map(blockProtocolToPayload),
      source: fullPayload.source ?? 'bdsa-protocols',
      version: fullPayload.version ?? '1.0',
    })
    await load()
  }

  const handleSave = async (block: BlockProtocol) => {
    const without = blockProtocols.filter((b) => b.id !== block.id)
    await persistBlocks([...without, block])
  }

  const handleDelete = async (block: BlockProtocol) => {
    if (!window.confirm(`Delete block protocol "${block.name}"?`)) return
    await persistBlocks(blockProtocols.filter((b) => b.id !== block.id))
  }

  if (loading) {
    return <p className="block-protocols-loading">Loading block protocols…</p>
  }

  return (
    <div className="block-protocols-panel">
      <header className="block-protocols-header">
        <div>
          <h2>Block (blocking) protocols</h2>
          <p>
            Define how physical tissue blocks map to one or more region protocols for{' '}
            <strong>{collectionLabel}</strong>. Use this when a single block contains multiple
            distinct brain regions (not just the default 1:1 survey block index).
          </p>
        </div>
        {canEdit && (
          <button
            type="button"
            className="block-protocols-add-btn"
            onClick={() => setEditing('new')}
            disabled={!fullPayload}
          >
            Add block protocol
          </button>
        )}
      </header>

      {slotCollision.lines.length > 0 && (
        <div className="block-abbrev-collision-banner" role="status">
          <strong>Abbreviation collision within block</strong>
          <ul>
            {slotCollision.lines.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
          <p className="block-abbrev-collision-hint">
            Slots in the same block need distinct region abbreviations (e.g. HIPP-L / HIPP-R).
            Saving is still allowed — fix the region protocols or remove a colliding slot.
          </p>
        </div>
      )}

      {!canEdit && (
        <p className="block-protocols-readonly-hint">
          Editing requires <code>VITE_BDSA_API_KEY</code> in the frontend environment.
        </p>
      )}

      {error && <p className="block-protocols-error">{error}</p>}

      {blockProtocols.length === 0 ? (
        <p className="block-protocols-empty">
          No block protocols defined. When empty, slide mappings fall back to survey block indices
          (REGION 1–N → region protocol list order).
        </p>
      ) : (
        <div className="block-protocols-table-wrap">
          <table className="block-protocols-table">
            <thead>
              <tr>
                <th>Block ID</th>
                <th>Name</th>
                <th>Regions in block</th>
                <th>Description</th>
                {canEdit && <th />}
              </tr>
            </thead>
            <tbody>
              {blockProtocols.map((block) => {
                const colliding = slotCollision.collidingBlockIds.has(block.id)
                return (
                  <tr
                    key={block.id}
                    className={colliding ? 'block-row-abbrev-collision' : undefined}
                    title={
                      colliding
                        ? 'Region abbreviations collide among slots in this block'
                        : undefined
                    }
                  >
                    <td>
                      <code>{block.id}</code>
                    </td>
                    <td>{block.name}</td>
                    <td className="block-protocols-regions-cell">
                      {formatBlockSlotsSummary(block, regionProtocols)}
                      {colliding && (
                        <div className="block-slot-collision-note">
                          Abbreviation collision in slots
                        </div>
                      )}
                    </td>
                    <td>{block.description || '—'}</td>
                    {canEdit && (
                      <td className="block-protocols-actions">
                        <button type="button" onClick={() => setEditing(block)}>
                          Edit
                        </button>
                        <button type="button" onClick={() => void handleDelete(block)}>
                          Delete
                        </button>
                      </td>
                    )}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {editing !== null && (
        <BlockProtocolModal
          block={editing === 'new' ? null : editing}
          collectionPrefix={collectionPrefix}
          regionProtocols={regionProtocols}
          existingIds={existingIds}
          onSave={handleSave}
          onClose={() => setEditing(null)}
        />
      )}
    </div>
  )
}
