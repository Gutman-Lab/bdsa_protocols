import { ProtocolDetailCard } from './ProtocolDetailCard'
import './ProtocolHoverPanel.css'

export function ProtocolHoverPanel({
  protocol,
  variant,
}: {
  protocol: Record<string, unknown> | null
  variant: 'stain' | 'region'
}) {
  return (
    <aside className="protocol-hover-panel" aria-live="polite">
      <h3 className="protocol-hover-panel-title">Protocol preview</h3>
      {protocol ? (
        <ProtocolDetailCard protocol={protocol} variant={variant} highlighted />
      ) : (
        <p className="protocol-hover-panel-hint">
          Hover a table row or protocol ID to preview hemisphere, slice thickness, landmarks,
          stain chemistry, and survey notes here — no need to switch tabs.
        </p>
      )}
    </aside>
  )
}
