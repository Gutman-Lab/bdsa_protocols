import { useState, useEffect } from 'react'
import { loadManuscriptContent, getManuscriptSection, type ManuscriptContent } from '../../utils/manuscriptLoader'
import SurveySummary from './SurveySummary'
import './DocumentationTabs.css'

type TabId = 'summary' | 'background' | 'methods' | 'references'

interface Tab {
  id: TabId
  label: string
}

const tabs: Tab[] = [
  { id: 'summary', label: 'Summary' },
  { id: 'background', label: 'Background' },
  { id: 'methods', label: 'Methods' },
  { id: 'references', label: 'References' }
]

export default function DocumentationTabs() {
  const [activeTab, setActiveTab] = useState<TabId>('summary')
  const [content, setContent] = useState<ManuscriptContent | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadManuscriptContent()
      .then(setContent)
      .catch((error) => {
        console.error('Failed to load manuscript content:', error)
      })
      .finally(() => setLoading(false))
  }, [])

  const getTabContent = (tabId: TabId): string => {
    if (loading) {
      return '<p>Loading content...</p>'
    }
    if (!content) {
      return '<p>Failed to load content. Please check that manuscript-first-submission.docx is available.</p>'
    }
    if (tabId === 'summary') {
      return '<p>Summary is shown above.</p>'
    }
    return getManuscriptSection(content, tabId)
  }

  return (
    <div className="documentation-tabs">
      <div className="tabs-header">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="tabs-content documentation-card">
        {activeTab === 'summary' && content?.summary ? (
          <SurveySummary summary={content.summary} />
        ) : (
          <div
            className="tab-panel"
            dangerouslySetInnerHTML={{ __html: getTabContent(activeTab) }}
          />
        )}
      </div>
    </div>
  )
}

