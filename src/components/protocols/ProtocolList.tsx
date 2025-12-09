import { useState, useEffect } from 'react'
import { Card, Button } from 'bdsa-react-components'
import './ProtocolList.css'

export interface Protocol {
  id: string
  name: string
  stainType: string
  region: string
  description: string
  createdAt: string
  updatedAt: string
}

interface ProtocolListProps {
  onEditProtocol: (protocolId: string) => void
}

export default function ProtocolList({ onEditProtocol }: ProtocolListProps) {
  const [protocols, setProtocols] = useState<Protocol[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // TODO: Replace with actual API call
    // For now, using mock data
    setTimeout(() => {
      setProtocols([
        {
          id: '1',
          name: 'H&E Standard',
          stainType: 'Hematoxylin & Eosin',
          region: 'General',
          description: 'Standard H&E staining protocol for general tissue examination',
          createdAt: '2024-01-15',
          updatedAt: '2024-01-15'
        },
        {
          id: '2',
          name: 'IHC CD3',
          stainType: 'Immunohistochemistry',
          region: 'Lymphoid',
          description: 'CD3 immunohistochemistry protocol for T-cell identification',
          createdAt: '2024-01-20',
          updatedAt: '2024-01-22'
        }
      ])
      setLoading(false)
    }, 500)
  }, [])

  if (loading) {
    return <div className="protocol-list-loading">Loading protocols...</div>
  }

  if (protocols.length === 0) {
    return (
      <Card className="protocol-list-empty">
        <p>No protocols found. Create your first protocol to get started.</p>
      </Card>
    )
  }

  return (
    <div className="protocol-list">
      {protocols.map((protocol) => (
        <Card key={protocol.id} className="protocol-card" hoverable>
          <div className="protocol-card-header">
            <h3>{protocol.name}</h3>
            <Button
              onClick={() => onEditProtocol(protocol.id)}
              variant="secondary"
              size="small"
            >
              Edit
            </Button>
          </div>
          <div className="protocol-card-content">
            <div className="protocol-meta">
              <span className="protocol-label">Stain Type:</span>
              <span>{protocol.stainType}</span>
            </div>
            <div className="protocol-meta">
              <span className="protocol-label">Region:</span>
              <span>{protocol.region}</span>
            </div>
            <p className="protocol-description">{protocol.description}</p>
            <div className="protocol-dates">
              <small>Created: {protocol.createdAt}</small>
              <small>Updated: {protocol.updatedAt}</small>
            </div>
          </div>
        </Card>
      ))}
    </div>
  )
}

