import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import ProtocolsPage from './pages/ProtocolsPage'
import DocumentationPage from './pages/DocumentationPage'
import './App.css'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/protocols" replace />} />
          <Route path="/protocols" element={<ProtocolsPage />} />
          <Route path="/documentation" element={<DocumentationPage />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App

