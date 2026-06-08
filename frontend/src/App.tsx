import { lazy, Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import DocumentationPage from './pages/DocumentationPage'
import SchemaPage from './pages/SchemaPage'
import SlideMappingsPage from './pages/SlideMappingsPage'
import './App.css'

const ProtocolsPage = lazy(() => import('./pages/ProtocolsPage'))

function PageFallback() {
  return <p className="route-loading">Loading…</p>
}

function App() {
  return (
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Layout>
        <Suspense fallback={<PageFallback />}>
          <Routes>
            <Route path="/" element={<Navigate to="/protocols" replace />} />
            <Route path="/protocols" element={<ProtocolsPage />} />
            <Route path="/documentation" element={<DocumentationPage />} />
            <Route path="/schema" element={<SchemaPage />} />
            <Route path="/slide-mappings" element={<SlideMappingsPage />} />
            <Route path="*" element={<Navigate to="/protocols" replace />} />
          </Routes>
        </Suspense>
      </Layout>
    </Router>
  )
}

export default App

