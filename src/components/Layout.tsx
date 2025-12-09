import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import './Layout.css'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()

  return (
    <div className="layout">
      <header className="layout-header">
        <div className="layout-header-content">
          <h1 className="layout-title">BDSA Protocols Platform</h1>
          <nav className="layout-nav">
            <Link
              to="/protocols"
              className={`nav-link ${location.pathname === '/protocols' ? 'active' : ''}`}
            >
              Protocols
            </Link>
            <Link
              to="/documentation"
              className={`nav-link ${location.pathname === '/documentation' ? 'active' : ''}`}
            >
              Documentation
            </Link>
          </nav>
        </div>
      </header>
      <main className="layout-main">
        {children}
      </main>
    </div>
  )
}

