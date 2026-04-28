import { useQueryClient } from '@tanstack/react-query'
import { NavLink } from 'react-router-dom'

import { ROLE_LABELS } from '../context/auth-context'
import { useAuth } from '../context/useAuth'
import { useGlobalFilters } from '../context/useGlobalFilters'

const navigationItems = [
  { to: '/imports', label: 'Import & Validation', short: 'CSV', roles: ['ADMIN_RH'] },
  { to: '/dashboard', label: 'Tableau de bord', short: 'KPI', roles: ['MANAGER_RH', 'DIRIGEANT'] },
  { to: '/analytics', label: 'Analyses avancees', short: 'EDA', roles: ['ANALYSTE_RH'] },
  { to: '/prediction', label: 'Prediction', short: 'ML', roles: ['MANAGER_RH'] },
  { to: '/report', label: 'Rapport PDF', short: 'PDF', roles: ['DIRIGEANT'] },
]

export function AppShell({ children }) {
  const queryClient = useQueryClient()
  const { activeCount } = useGlobalFilters()
  const { hasRole, logout, user } = useAuth()
  const visibleNavigationItems = navigationItems.filter((item) => hasRole(item.roles))

  function handleLogout() {
    queryClient.clear()
    logout()
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <p className="eyebrow">Analyse RH</p>
          <h1>Pulse Workforce</h1>
          <p className="brand-copy">
            Un cockpit analytique pour fiabiliser les donnees, suivre les KPI et anticiper les departs.
          </p>
        </div>

        <nav className="side-nav">
          {visibleNavigationItems.map((item) => (
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

        <div className="sidebar-card user-card">
          <span className="sidebar-card-label">Session active</span>
          <strong>{user?.fullName}</strong>
          <p>{ROLE_LABELS[user?.role] || user?.role}</p>
          <button className="ghost-button logout-button" type="button" onClick={handleLogout}>
            Deconnexion
          </button>
        </div>

        <div className="sidebar-card">
          <span className="sidebar-card-label">Filtres globaux actifs</span>
          <strong>{activeCount}</strong>
          <p>Les filtres s'appliquent au dashboard, aux analyses, aux predictions et au rapport.</p>
        </div>
      </aside>

      <div className="main-layout">
        <header className="topbar">
          <div>
            <p className="eyebrow">Projet federateur</p>
            <h2>Analyse et visualisation des donnees RH</h2>
          </div>
        </header>

        <main className="page-content">{children}</main>
      </div>
    </div>
  )
}
