import {
  REGION_SUMMARY_KEYS,
  STAIN_SUMMARY_KEYS,
  extraProtocolFields,
  protocolField,
} from '../../utils/protocolDisplay'
import './ProtocolDefinitionsTab.css'

export function ProtocolDetailCard({
  protocol,
  variant = 'region',
  highlighted = false,
}: {
  protocol: Record<string, unknown>
  variant?: 'stain' | 'region'
  highlighted?: boolean
}) {
  const summaryKeys = variant === 'stain' ? STAIN_SUMMARY_KEYS : REGION_SUMMARY_KEYS
  const known = summaryKeys.map((c) => c.key)
  const extras = extraProtocolFields(protocol, known)

  return (
    <article
      className={`protocol-def-card ${highlighted ? 'protocol-def-card-highlighted' : ''}`}
    >
      <header className="protocol-def-card-header">
        <h4>{String(protocol.name ?? protocol.id)}</h4>
        <code>{String(protocol.id)}</code>
      </header>
      {protocol.description ? (
        <p className="protocol-def-description">{String(protocol.description)}</p>
      ) : null}
      <dl className="protocol-def-dl">
        {summaryKeys.map((col) => (
          <div key={col.key} className="protocol-def-row">
            <dt>{col.label}</dt>
            <dd>{protocolField(protocol, col.key)}</dd>
          </div>
        ))}
        {extras.map(({ key, value }) => (
          <div key={key} className="protocol-def-row">
            <dt>{key}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
    </article>
  )
}
