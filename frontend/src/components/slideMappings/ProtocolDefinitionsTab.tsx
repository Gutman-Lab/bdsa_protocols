import { ProtocolDetailCard } from './ProtocolDetailCard'
import './ProtocolDefinitionsTab.css'

export function ProtocolDefinitionsTab({
  stainProtocols,
  regionProtocols,
  hoveredProtocolId = null,
  onProtocolHover,
}: {
  stainProtocols: Record<string, unknown>[]
  regionProtocols: Record<string, unknown>[]
  hoveredProtocolId?: string | null
  onProtocolHover?: (id: string | null) => void
}) {
  return (
    <div className="protocol-definitions-tab">
      <section className="slide-mappings-section">
        <h3>Region protocol definitions ({regionProtocols.length})</h3>
        <p className="slide-mappings-section-desc">
          Full region protocol metadata from the API — hemisphere, slice thickness, orientation,
          landmarks, and survey notes. Sourced from the center&apos;s ADRC neuropath survey import.
        </p>
        {regionProtocols.length === 0 ? (
          <p className="slide-mappings-empty">No region protocols defined.</p>
        ) : (
          <div className="protocol-def-grid">
            {regionProtocols.map((protocol) => {
              const id = String(protocol.id)
              return (
                <div
                  key={id}
                  onMouseEnter={() => onProtocolHover?.(id)}
                  onMouseLeave={() => onProtocolHover?.(null)}
                >
                  <ProtocolDetailCard
                    protocol={protocol}
                    variant="region"
                    highlighted={hoveredProtocolId === id}
                  />
                </div>
              )
            })}
          </div>
        )}
      </section>

      <section className="slide-mappings-section">
        <h3>Stain protocol definitions ({stainProtocols.length})</h3>
        <p className="slide-mappings-section-desc">
          Stain chemistry, antibody, and chromogen details for each stain protocol at this center.
        </p>
        {stainProtocols.length === 0 ? (
          <p className="slide-mappings-empty">No stain protocols defined.</p>
        ) : (
          <div className="protocol-def-grid">
            {stainProtocols.map((protocol) => {
              const id = String(protocol.id)
              return (
                <div
                  key={id}
                  onMouseEnter={() => onProtocolHover?.(id)}
                  onMouseLeave={() => onProtocolHover?.(null)}
                >
                  <ProtocolDetailCard
                    protocol={protocol}
                    variant="stain"
                    highlighted={hoveredProtocolId === id}
                  />
                </div>
              )
            })}
          </div>
        )}
      </section>
    </div>
  )
}
