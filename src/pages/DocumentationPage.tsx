import { useState } from 'react'
import DocumentationTabs from '../components/documentation/DocumentationTabs'
import './DocumentationPage.css'

export default function DocumentationPage() {
  return (
    <div className="documentation-page">
      <h2>BDSA Platform Documentation</h2>
      <DocumentationTabs />
    </div>
  )
}

