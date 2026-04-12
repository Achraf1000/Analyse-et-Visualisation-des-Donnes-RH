import { NavLink } from 'react-router-dom'

import { useGlobalFilters } from '../context/useGlobalFilters'

const navigationItems = [
  { to: '/imports', label: 'Import & Validation', short: 'CSV' },
  { to: '/dashboard', label: 'Tableau de bord', short: 'KPI' },
  { to: '/analytics', label: 'Analyses avancées', short: 'EDA' },
  { to: '/prediction', label: 'Prédiction', short: 'ML' },
  { to: '/report', label: 'Rapport PDF', short: 'PDF' },
]

export function AppShell({ children }) {
  const { activeCount } = useGlobalFilters()

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <p className="eyebrow">Analyse RH</p>
          <h1>Pulse Workforce</h1>
          <p className="brand-copy">
            Un cockpit analytique pour fiabiliser les données, suivre les KPI et anticiper les départs.
          </p>
        </div>

        <nav className="side-nav">
          {navigationItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `nav-item ${isActive ? 'is-active' : ''}`}
            >
              <span className="nav-item-short">{item.short}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-card">
          <span className="sidebar-card-label">Filtres globaux actifs</span>
          <strong>{activeCount}</strong>
          <p>Les filtres s’appliquent au dashboard, aux analyses, aux prédictions et au rapport.</p>
        </div>
      </aside>

      <div className="main-layout">
        <header className="topbar">
          <div>
            <p className="eyebrow">Projet fédérateur</p>
            <h2>Analyse et visualisation des données RH</h2>
          </div>
          <div className="topbar-badge">
            <span>Stack</span>
            <strong>React + FastAPI</strong>
          </div>
        </header>

        <main className="page-content">{children}</main>
      </div>
    </div>
  )
}
