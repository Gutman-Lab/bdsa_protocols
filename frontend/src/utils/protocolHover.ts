export type ProtocolHoverHandlers = {
  className: string
  onMouseEnter: () => void
  onMouseLeave: () => void
}

export function protocolRowHoverHandlers(
  protocolId: string,
  highlightedProtocolId: string | null,
  onProtocolHover: (id: string | null) => void,
): ProtocolHoverHandlers {
  const highlighted = highlightedProtocolId === protocolId
  return {
    className: highlighted ? 'slide-mappings-row-highlighted' : '',
    onMouseEnter: () => onProtocolHover(protocolId),
    onMouseLeave: () => onProtocolHover(null),
  }
}

export function findProtocolById(
  stainProtocols: Record<string, unknown>[],
  regionProtocols: Record<string, unknown>[],
  id: string | null,
): { protocol: Record<string, unknown>; variant: 'stain' | 'region' } | null {
  if (!id) return null
  const stain = stainProtocols.find((p) => p.id === id)
  if (stain) return { protocol: stain, variant: 'stain' }
  const region = regionProtocols.find((p) => p.id === id)
  if (region) return { protocol: region, variant: 'region' }
  return null
}
