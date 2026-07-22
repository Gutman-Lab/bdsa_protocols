import { useEffect, useState } from 'react'

export function CaseIdAliasCell({
  value,
  label,
  hint,
  disabled,
  saving,
  onSave,
}: {
  value: string | undefined
  label: string
  hint: string
  disabled?: boolean
  saving?: boolean
  onSave: (next: string | null) => Promise<void>
}) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(value ?? '')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!editing) setDraft(value ?? '')
  }, [value, editing])

  const startEdit = () => {
    if (disabled || saving) return
    setDraft(value ?? '')
    setError(null)
    setEditing(true)
  }

  const cancel = () => {
    setDraft(value ?? '')
    setError(null)
    setEditing(false)
  }

  const save = async () => {
    const trimmed = draft.trim()
    const next = trimmed || null
    if (next === (value ?? null) || (next === null && !value)) {
      setEditing(false)
      return
    }
    setError(null)
    try {
      await onSave(next)
      setEditing(false)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }

  if (editing) {
    return (
      <div className="case-alias-cell case-alias-cell-editing">
        <input
          type="text"
          className="case-alias-input"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={hint}
          aria-label={`${label} for case`}
          disabled={saving}
          onKeyDown={(e) => {
            if (e.key === 'Enter') void save()
            if (e.key === 'Escape') cancel()
          }}
          autoFocus
        />
        <div className="case-alias-actions">
          <button
            type="button"
            className="case-alias-btn case-alias-btn-save"
            onClick={() => void save()}
            disabled={saving}
          >
            {saving ? '…' : 'Save'}
          </button>
          <button
            type="button"
            className="case-alias-btn"
            onClick={cancel}
            disabled={saving}
          >
            Cancel
          </button>
        </div>
        {error && <p className="case-alias-error">{error}</p>}
      </div>
    )
  }

  return (
    <div className="case-alias-cell">
      {value ? (
        <code>{value}</code>
      ) : (
        <span className="slide-mappings-muted">—</span>
      )}
      {!disabled && (
        <button
          type="button"
          className="case-alias-edit-btn"
          onClick={startEdit}
          title={value ? `Edit ${label}` : `Add ${label}`}
          aria-label={value ? `Edit ${label}` : `Add ${label}`}
        >
          {value ? 'Edit' : 'Add'}
        </button>
      )}
    </div>
  )
}
