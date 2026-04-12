import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'

import { AppShell } from './components/AppShell'

const ImportPage = lazy(() => import('./pages/ImportPage').then((module) => ({ default: module.ImportPage })))
const DashboardPage = lazy(() => import('./pages/DashboardPage').then((module) => ({ default: module.DashboardPage })))
const AnalyticsPage = lazy(() => import('./pages/AnalyticsPage').then((module) => ({ default: module.AnalyticsPage })))
const PredictionPage = lazy(() => import('./pages/PredictionPage').then((module) => ({ default: module.PredictionPage })))
const ReportPage = lazy(() => import('./pages/ReportPage').then((module) => ({ default: module.ReportPage })))

export default function App() {
  return (
    <AppShell>
      <Suspense fallback={<div className="loading-card">Chargement de la page...</div>}>
        <Routes>
          <Route path="/" element={<Navigate to="/imports" replace />} />
          <Route path="/imports" element={<ImportPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/prediction" element={<PredictionPage />} />
          <Route path="/report" element={<ReportPage />} />
        </Routes>
      </Suspense>
    </AppShell>
  )
}
