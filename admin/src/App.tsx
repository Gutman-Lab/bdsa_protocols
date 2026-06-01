import { useEffect, useState } from 'react'
import {
  getApiUrl,
  fetchCollections,
  fetchBackupStatus,
  downloadMongoBackup,
  saveMongoBackupOnServer,
} from './api'
import { CollectionsTab } from './tabs/CollectionsTab'
import { ProtocolsTab } from './tabs/ProtocolsTab'
import { CaseMappingsTab } from './tabs/CaseMappingsTab'
import { PatientMappingsTab } from './tabs/PatientMappingsTab'
import { SlidesTab } from './tabs/SlidesTab'
import { Block2RegionTab } from './tabs/Block2RegionTab'
import './App.css'

const TABS = [
  { id: 'collections', label: 'Collections' },
  { id: 'protocols', label: 'Protocols' },
  { id: 'case-mappings', label: 'Case ID Mappings' },
  { id: 'patient-mappings', label: 'Patient ID Mappings' },
  { id: 'slides', label: 'Slides' },
  { id: 'block2region', label: 'Block → Region' },
] as const

type TabId = (typeof TABS)[number]['id']

function App() {
  const [activeTab, setActiveTab] = useState<TabId>('collections')
  const [collectionId, setCollectionId] = useState<string>('')
  const [collectionIds, setCollectionIds] = useState<string[]>([])
  const [loadingCollections, setLoadingCollections] = useState(true)
  const [backupBusy, setBackupBusy] = useState(false)
  const [serverBackupEnabled, setServerBackupEnabled] = useState(false)

  useEffect(() => {
    fetchBackupStatus()
      .then((s) => setServerBackupEnabled(s.backupDirConfigured))
      .catch(() => setServerBackupEnabled(false))
  }, [])

  const refreshCollections = () => {
    fetchCollections()
      .then((r) => setCollectionIds(r.collection_ids || []))
      .catch(() => setCollectionIds([]))
      .finally(() => setLoadingCollections(false))
  }

  useEffect(() => {
    refreshCollections()
  }, [])

  const needsCollection = activeTab !== 'collections'

  const formatCounts = (counts: Record<string, number>) =>
    Object.entries(counts)
      .filter(([, n]) => n > 0)
      .map(([k, n]) => `${k}: ${n}`)
      .join(', ') || 'no documents'

  const handleDownloadBackup = async () => {
    setBackupBusy(true)
    try {
      const { filename, counts } = await downloadMongoBackup()
      alert(`Backup downloaded: ${filename}\n\n${formatCounts(counts)}`)
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e)
      alert(`Backup failed: ${msg}`)
    } finally {
      setBackupBusy(false)
    }
  }

  const handleSaveBackupOnServer = async () => {
    setBackupBusy(true)
    try {
      const result = await saveMongoBackupOnServer()
      alert(
        `Backup saved on server:\n${result.filename}\n\n${result.path}\n\n${formatCounts(result.counts)}`,
      )
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e)
      alert(`Server backup failed: ${msg}`)
    } finally {
      setBackupBusy(false)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header-row">
          <div>
            <h1>BDSA Protocols – Admin</h1>
            <p className="app-api">API: {getApiUrl()}</p>
          </div>
          <div className="app-backup-actions">
            <button
              type="button"
              className="app-backup-btn"
              onClick={handleDownloadBackup}
              disabled={backupBusy}
              title="Download all MongoDB data as JSON"
            >
              {backupBusy ? 'Backing up…' : 'Download backup'}
            </button>
            {serverBackupEnabled && (
              <button
                type="button"
                className="app-backup-btn app-backup-btn-secondary"
                onClick={handleSaveBackupOnServer}
                disabled={backupBusy}
                title="Also write JSON under backups/ on the API host"
              >
                Save to server
              </button>
            )}
          </div>
        </div>
      </header>

      {needsCollection && (
        <div className="app-collection-bar">
          <label htmlFor="collection-select">
            Collection:
          </label>
          <select
            id="collection-select"
            value={collectionId}
            onChange={(e) => setCollectionId(e.target.value)}
            disabled={loadingCollections}
          >
            <option value="">Select…</option>
            {collectionIds.map((id) => (
              <option key={id} value={id}>
                {id}
              </option>
            ))}
          </select>
          {collectionIds.length === 0 && !loadingCollections && (
            <span className="app-hint">No collections yet. Create data via API.</span>
          )}
        </div>
      )}

      <nav className="app-tabs">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={`app-tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <main className="app-main">
        {activeTab === 'collections' && <CollectionsTab onCollectionsChange={refreshCollections} />}
        {activeTab === 'protocols' && <ProtocolsTab collectionId={collectionId || null} />}
        {activeTab === 'case-mappings' && <CaseMappingsTab collectionId={collectionId || null} />}
        {activeTab === 'patient-mappings' && <PatientMappingsTab collectionId={collectionId || null} />}
        {activeTab === 'slides' && <SlidesTab collectionId={collectionId || null} />}
        {activeTab === 'block2region' && <Block2RegionTab collectionId={collectionId || null} />}
      </main>
    </div>
  )
}

export default App
