import { useState } from 'react'
import { Card, Button } from 'bdsa-react-components'
import ProtocolList from '../components/protocols/ProtocolList'
import ProtocolEditor from '../components/protocols/ProtocolEditor'
import './ProtocolsPage.css'

export default function ProtocolsPage() {
  const [viewMode, setViewMode] = useState<'list' | 'create' | 'edit'>('list')
  const [selectedProtocol, setSelectedProtocol] = useState<string | null>(null)

  const handleCreateNew = () => {
    setSelectedProtocol(null)
    setViewMode('create')
  }

  const handleEditProtocol = (protocolId: string) => {
    setSelectedProtocol(protocolId)
    setViewMode('edit')
  }

  const handleBackToList = () => {
    setViewMode('list')
    setSelectedProtocol(null)
  }

  return (
    <div className="protocols-page">
      {viewMode === 'list' ? (
        <div className="protocols-list-view">
          <div className="protocols-header">
            <h2>Stain and Region Protocols</h2>
            <Button onClick={handleCreateNew} variant="primary">
              Create New Protocol
            </Button>
          </div>
          <ProtocolList onEditProtocol={handleEditProtocol} />
        </div>
      ) : (
        <div className="protocols-editor-view">
          <div className="protocols-editor-header">
            <Button onClick={handleBackToList} variant="secondary">
              ← Back to Protocols
            </Button>
            <h2>{viewMode === 'create' ? 'Create New Protocol' : 'Edit Protocol'}</h2>
          </div>
          <ProtocolEditor
            protocolId={selectedProtocol}
            mode={viewMode}
            onSave={handleBackToList}
            onCancel={handleBackToList}
          />
        </div>
      )}
    </div>
  )
}

