import { useState, useEffect } from 'react'
import { Card, Button } from 'bdsa-react-components'
import './ProtocolEditor.css'

interface ProtocolEditorProps {
  protocolId: string | null
  mode: 'create' | 'edit'
  onSave: () => void
  onCancel: () => void
}

interface ProtocolFormData {
  name: string
  stainType: string
  region: string
  description: string
  steps: ProtocolStep[]
}

interface ProtocolStep {
  id: string
  order: number
  title: string
  description: string
  duration: string
  temperature: string
}

export default function ProtocolEditor({
  protocolId,
  mode,
  onSave,
  onCancel
}: ProtocolEditorProps) {
  const [formData, setFormData] = useState<ProtocolFormData>({
    name: '',
    stainType: '',
    region: '',
    description: '',
    steps: []
  })
  const [loading, setLoading] = useState(mode === 'edit')

  useEffect(() => {
    if (mode === 'edit' && protocolId) {
      // TODO: Replace with actual API call
      // For now, using mock data
      setTimeout(() => {
        setFormData({
          name: 'H&E Standard',
          stainType: 'Hematoxylin & Eosin',
          region: 'General',
          description: 'Standard H&E staining protocol',
          steps: [
            {
              id: '1',
              order: 1,
              title: 'Deparaffinization',
              description: 'Remove paraffin from tissue sections',
              duration: '10 min',
              temperature: '60°C'
            }
          ]
        })
        setLoading(false)
      }, 500)
    }
  }, [mode, protocolId])

  const handleInputChange = (field: keyof ProtocolFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleAddStep = () => {
    const newStep: ProtocolStep = {
      id: Date.now().toString(),
      order: formData.steps.length + 1,
      title: '',
      description: '',
      duration: '',
      temperature: ''
    }
    setFormData(prev => ({
      ...prev,
      steps: [...prev.steps, newStep]
    }))
  }

  const handleStepChange = (stepId: string, field: keyof ProtocolStep, value: string | number) => {
    setFormData(prev => ({
      ...prev,
      steps: prev.steps.map(step =>
        step.id === stepId ? { ...step, [field]: value } : step
      )
    }))
  }

  const handleRemoveStep = (stepId: string) => {
    setFormData(prev => ({
      ...prev,
      steps: prev.steps.filter(step => step.id !== stepId)
    }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // TODO: Implement actual save logic
    console.log('Saving protocol:', formData)
    onSave()
  }

  if (loading) {
    return <div className="protocol-editor-loading">Loading protocol...</div>
  }

  return (
    <form onSubmit={handleSubmit} className="protocol-editor">
      <Card className="protocol-editor-form">
        <div className="form-section">
          <h3>Basic Information</h3>
          <div className="form-group">
            <label htmlFor="name">Protocol Name</label>
            <input
              id="name"
              type="text"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="stainType">Stain Type</label>
            <input
              id="stainType"
              type="text"
              value={formData.stainType}
              onChange={(e) => handleInputChange('stainType', e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="region">Region</label>
            <input
              id="region"
              type="text"
              value={formData.region}
              onChange={(e) => handleInputChange('region', e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="description">Description</label>
            <textarea
              id="description"
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              rows={4}
              required
            />
          </div>
        </div>

        <div className="form-section">
          <div className="form-section-header">
            <h3>Protocol Steps</h3>
            <Button type="button" onClick={handleAddStep} variant="secondary" size="small">
              Add Step
            </Button>
          </div>
          {formData.steps.length === 0 ? (
            <p className="no-steps">No steps added yet. Click "Add Step" to begin.</p>
          ) : (
            <div className="steps-list">
              {formData.steps.map((step, index) => (
                <Card key={step.id} className="step-card">
                  <div className="step-header">
                    <span className="step-number">Step {step.order}</span>
                    <Button
                      type="button"
                      onClick={() => handleRemoveStep(step.id)}
                      variant="danger"
                      size="small"
                    >
                      Remove
                    </Button>
                  </div>
                  <div className="step-fields">
                    <div className="form-group">
                      <label>Title</label>
                      <input
                        type="text"
                        value={step.title}
                        onChange={(e) => handleStepChange(step.id, 'title', e.target.value)}
                        required
                      />
                    </div>
                    <div className="form-group">
                      <label>Description</label>
                      <textarea
                        value={step.description}
                        onChange={(e) => handleStepChange(step.id, 'description', e.target.value)}
                        rows={2}
                        required
                      />
                    </div>
                    <div className="step-meta">
                      <div className="form-group">
                        <label>Duration</label>
                        <input
                          type="text"
                          value={step.duration}
                          onChange={(e) => handleStepChange(step.id, 'duration', e.target.value)}
                          placeholder="e.g., 10 min"
                        />
                      </div>
                      <div className="form-group">
                        <label>Temperature</label>
                        <input
                          type="text"
                          value={step.temperature}
                          onChange={(e) => handleStepChange(step.id, 'temperature', e.target.value)}
                          placeholder="e.g., 60°C"
                        />
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>

        <div className="form-actions">
          <Button type="button" onClick={onCancel} variant="secondary">
            Cancel
          </Button>
          <Button type="submit" variant="primary">
            {mode === 'create' ? 'Create Protocol' : 'Save Changes'}
          </Button>
        </div>
      </Card>
    </form>
  )
}

