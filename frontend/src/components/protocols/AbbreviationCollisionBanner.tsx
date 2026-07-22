import { useMemo } from 'react'
import { useProtocols } from 'bdsa-react-components'
import {
  analyzeRegionAbbreviations,
  analyzeStainAbbreviations,
  formatCollisionSummary,
} from '../../utils/protocolAbbreviations'
import './AbbreviationCollisionBanner.css'

/**
 * Warn-only banner for duplicate region/stain abbreviations in the active collection.
 * Must render inside ProtocolProvider.
 */
export function AbbreviationCollisionBanner() {
  const { regionProtocols, stainProtocols, loading } = useProtocols()

  const regionAnalysis = useMemo(
    () =>
      analyzeRegionAbbreviations(
        regionProtocols as unknown as Record<string, unknown>[],
      ),
    [regionProtocols],
  )

  const stainAnalysis = useMemo(
    () =>
      analyzeStainAbbreviations(
        stainProtocols as unknown as Record<string, unknown>[],
      ),
    [stainProtocols],
  )

  const lines = useMemo(() => {
    const out: string[] = []
    out.push(...formatCollisionSummary('region', regionAnalysis.collisions))
    out.push(...formatCollisionSummary('stain', stainAnalysis.collisions))
    if (regionAnalysis.missing.protocolIds.length > 0) {
      const n = regionAnalysis.missing.protocolIds.length
      out.push(
        `${n} region protocol${n === 1 ? '' : 's'} missing abbreviation` +
          (n <= 5
            ? `: ${regionAnalysis.missing.names.join(', ')}`
            : ` (e.g. ${regionAnalysis.missing.names.slice(0, 3).join(', ')}…)`),
      )
    }
    return out
  }, [regionAnalysis, stainAnalysis])

  if (loading || lines.length === 0) return null

  const hasCollisions =
    regionAnalysis.collisions.length > 0 || stainAnalysis.collisions.length > 0

  return (
    <div
      className={`abbrev-collision-banner${hasCollisions ? ' abbrev-collision-banner-warn' : ' abbrev-collision-banner-note'}`}
      role="status"
    >
      <strong>
        {hasCollisions
          ? 'Abbreviation collision'
          : 'Abbreviation note'}
      </strong>
      <ul>
        {lines.map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ul>
      {hasCollisions && (
        <p className="abbrev-collision-hint">
          Filename tokens must be unique within regions and within stains (e.g. use{' '}
          <code>HIPP-L</code> / <code>HIPP-R</code> for left/right hippocampus). Saving is still
          allowed.
        </p>
      )}
    </div>
  )
}
