import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'

import { AppShell } from './components/AppShell'
import { useAuth } from './context/useAuth'
import { LoginPage } from './pages/LoginPage'

const ImportPage = lazy(() => import('./pages/ImportPage').then((module) => ({ default: module.ImportPage })))
const DashboardPage = lazy(() => import('./pages/DashboardPage').then((module) => ({ default: module.DashboardPage })))
const AnalyticsPage = lazy(() => import('./pages/AnalyticsPage').then((module) => ({ default: module.AnalyticsPage })))
const PredictionPage = lazy(() => import('./pages/PredictionPage').then((module) => ({ default: module.PredictionPage })))
const ReportPage = lazy(() => import('./pages/ReportPage').then((module) => ({ default: module.ReportPage })))

function ProtectedRoute({ children, roles }) {
  const location = useLocation()
  const { hasRole, isAuthenticated, isReady } = useAuth()

  if (!isReady) {
    return <div className="loading-card">Verification de la session...</div>
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (roles && !hasRole(roles)) {
    return <Navigate to="/forbidden" replace />
  }

  return children
}

function ProtectedPage({ children, roles }) {
  return (
    <ProtectedRoute roles={roles}>
      <AppShell>{children}</AppShell>
    </ProtectedRoute>
  )
}

function RoleRedirect() {
  const { defaultPath, isAuthenticated, isReady } = useAuth()

  if (!isReady) {
    return <div className="loading-card">Verification de la session...</div>
  }

  return <Navigate to={isAuthenticated ? defaultPath : '/login'} replace />
}

function ForbiddenPage() {
  return (
    <section className="empty-card empty-card-emphasis">
      <h3>Acces refuse</h3>
      <p>Votre role ne permet pas d'acceder a ce module.</p>
    </section>
  )
}

export default function App() {
  return (
    <Suspense fallback={<div className="loading-card">Chargement de la page...</div>}>
      <Routes>
        <Route path="/" element={<RoleRedirect />} />
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/forbidden"
          element={
            <ProtectedPage>
              <ForbiddenPage />
            </ProtectedPage>
          }
        />
        <Route
          path="/imports"
          element={
            <ProtectedPage roles={['ADMIN_RH']}>
              <ImportPage />
            </ProtectedPage>
          }
        />
        <Route
          path="/dashboard"
          element={
            <ProtectedPage roles={['MANAGER_RH', 'DIRIGEANT']}>
              <DashboardPage />
            </ProtectedPage>
          }
        />
        <Route
          path="/analytics"
          element={
            <ProtectedPage roles={['ANALYSTE_RH']}>
              <AnalyticsPage />
            </ProtectedPage>
          }
        />
        <Route
          path="/prediction"
          element={
            <ProtectedPage roles={['MANAGER_RH']}>
              <PredictionPage />
            </ProtectedPage>
          }
        />
        <Route
          path="/report"
          element={
            <ProtectedPage roles={['DIRIGEANT']}>
              <ReportPage />
            </ProtectedPage>
          }
        />
        <Route path="*" element={<RoleRedirect />} />
      </Routes>
    </Suspense>
  )
}
