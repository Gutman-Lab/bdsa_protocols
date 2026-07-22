import { useEffect, useMemo, useState } from 'react'
import {
  type BlockProtocol,
  type BlockProtocolSlot,
  suggestBlockProtocolId,
} from '../../utils/blockProtocols'
import { analyzeBlockSlotAbbreviationCollisions } from '../../utils/protocolAbbreviations'

export function BlockProtocolModal({
  block,
  collectionPrefix,
  regionProtocols,
  existingIds,
  onSave,
  onClose,
}: {
  block: BlockProtocol | null
  collectionPrefix: string
  regionProtocols: Record<string, unknown>[]
  existingIds: string[]
  onSave: (block: BlockProtocol) => Promise<void>
  onClose: () => void
}) {
  const isNew = !block
  const [id, setId] = useState(block?.id ?? '')
  const [name, setName] = useState(block?.name ?? '')
  const [description, setDescription] = useState(block?.description ?? '')
  const [slots, setSlots] = useState<BlockProtocolSlot[]>(block?.slots ?? [])
  const [pickRegionId, setPickRegionId] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setId(block?.id ?? '')
    setName(block?.name ?? '')
    setDescription(block?.description ?? '')
    setSlots(block?.slots ?? [])
    setError(null)
  }, [block])

  const availableRegions = useMemo(() => {
    const used = new Set(slots.map((s) => s.regionProtocolId))
    return regionProtocols.filter((p) => !used.has(String(p.id)))
  }, [regionProtocols, slots])

  const draftSlotCollision = useMemo(
    () =>
      analyzeBlockSlotAbbreviationCollisions(
        [{ id: id || 'draft', name: name || 'This block', slots }],
        regionProtocols,
      ),
    [id, name, slots, regionProtocols],
  )

  const addSlot = () => {
    if (!pickRegionId) return
    setSlots((prev) => [...prev, { regionProtocolId: pickRegionId }])
    setPickRegionId('')
  }

  const moveSlot = (index: number, direction: -1 | 1) => {
    setSlots((prev) => {
      const next = [...prev]
      const target = index + direction
      if (target < 0 || target >= next.length) return prev
      ;[next[index], next[target]] = [next[target], next[index]]
      return next
    })
  }

  const removeSlot = (index: number) => {
    setSlots((prev) => prev.filter((_, i) => i !== index))
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    const trimmedName = name.trim()
    if (!trimmedName) {
      setError('Name is required')
      return
    }
    if (!slots.length) {
      setError('Add at least one region protocol to this block')
      return
    }

    const blockId =
      id.trim() ||
      suggestBlockProtocolId(
        collectionPrefix,
        trimmedName,
        existingIds.filter((existing) => existing !== block?.id),
      )

    setSaving(true)
    setError(null)
    try {
      await onSave({
        id: blockId,
        type: 'block',
        name: trimmedName,
        description: description.trim() || undefined,
        slots,
      })
      onClose()
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="block-protocol-modal-backdrop" onClick={onClose} role="presentation">
      <div
        className="block-protocol-modal"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-labelledby="block-protocol-modal-title"
      >
        <header className="block-protocol-modal-header">
          <h3 id="block-protocol-modal-title">
            {isNew ? 'New block protocol' : 'Edit block protocol'}
          </h3>
          <button type="button" className="block-protocol-modal-close" onClick={onClose}>
            ×
          </button>
        </header>

        <form className="block-protocol-modal-form" onSubmit={(e) => void handleSubmit(e)}>
          <label>
            Name
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Hippocampus + amygdala composite block"
              required
            />
          </label>

          <label>
            Protocol ID
            <input
              type="text"
              value={id}
              onChange={(e) => setId(e.target.value)}
              placeholder="Auto-generated from name if left blank"
              disabled={!isNew}
            />
          </label>

          <label>
            Description
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              placeholder="Optional notes for QC or blocking SOP"
            />
          </label>

          <fieldset className="block-protocol-slots-fieldset">
            <legend>Regions in this block (ordered)</legend>
            <p className="block-protocol-slots-hint">
              A blocking protocol defines which region protocols are sampled together in one
              physical block. Order matches sectioning / staining workflow when relevant.
            </p>

            {slots.length === 0 ? (
              <p className="block-protocol-slots-empty">No regions added yet.</p>
            ) : (
              <ol className="block-protocol-slots-list">
                {slots.map((slot, index) => {
                  const region = regionProtocols.find(
                    (p) => String(p.id) === slot.regionProtocolId,
                  )
                  const abbrev = region?.abbreviation
                    ? String(region.abbreviation)
                    : null
                  return (
                    <li key={`${slot.regionProtocolId}-${index}`}>
                      <span className="block-protocol-slot-label">
                        {index + 1}. {String(region?.name ?? slot.regionProtocolId)}{' '}
                        {abbrev && <code title="Abbreviation">{abbrev}</code>}{' '}
                        <code>{slot.regionProtocolId}</code>
                      </span>
                      <div className="block-protocol-slot-actions">
                        <button
                          type="button"
                          onClick={() => moveSlot(index, -1)}
                          disabled={index === 0}
                          title="Move up"
                        >
                          ↑
                        </button>
                        <button
                          type="button"
                          onClick={() => moveSlot(index, 1)}
                          disabled={index === slots.length - 1}
                          title="Move down"
                        >
                          ↓
                        </button>
                        <button type="button" onClick={() => removeSlot(index)}>
                          Remove
                        </button>
                      </div>
                    </li>
                  )
                })}
              </ol>
            )}

            {draftSlotCollision.lines.length > 0 && (
              <div className="block-protocol-slot-collision-warn" role="status">
                Abbreviation collision in these slots (save still allowed):
                <ul>
                  {draftSlotCollision.lines.map((line) => (
                    <li key={line}>{line}</li>
                  ))}
                </ul>
              </div>
            )}

            {regionProtocols.length === 0 ? (
              <p className="block-protocol-slots-empty">
                Define region protocols first (Edit protocols tab).
              </p>
            ) : availableRegions.length === 0 && slots.length > 0 ? (
              <p className="block-protocol-slots-empty">
                All region protocols are already in this block.
              </p>
            ) : (
              <div className="block-protocol-add-slot">
                <select
                  value={pickRegionId}
                  onChange={(e) => setPickRegionId(e.target.value)}
                  disabled={!availableRegions.length}
                >
                  <option value="">Add region protocol…</option>
                  {availableRegions.map((region) => {
                    const abbrev = region.abbreviation
                      ? ` [${String(region.abbreviation)}]`
                      : ''
                    return (
                      <option key={String(region.id)} value={String(region.id)}>
                        {String(region.name ?? region.id)}
                        {abbrev}
                      </option>
                    )
                  })}
                </select>
                <button type="button" onClick={addSlot} disabled={!pickRegionId}>
                  Add
                </button>
              </div>
            )}
          </fieldset>

          {error && <p className="block-protocol-modal-error">{error}</p>}

          <footer className="block-protocol-modal-footer">
            <button type="button" onClick={onClose} disabled={saving}>
              Cancel
            </button>
            <button type="submit" className="block-protocol-save-btn" disabled={saving}>
              {saving ? 'Saving…' : 'Save block protocol'}
            </button>
          </footer>
        </form>
      </div>
    </div>
  )
}
