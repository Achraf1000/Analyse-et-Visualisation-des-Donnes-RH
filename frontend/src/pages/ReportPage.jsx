import { useDeferredValue } from 'react'
import { useQuery } from '@tanstack/react-query'

import { FilterBar } from '../components/FilterBar'
import { KPIGrid } from '../components/KPIGrid'
import { useGlobalFilters } from '../context/useGlobalFilters'
import { api, getReportUrl } from '../lib/api'
import { formatDateTime } from '../lib/format'

export function ReportPage() {
  const { filters } = useGlobalFilters()
  const deferredFilters = useDeferredValue(filters)

  const dashboardQuery = useQuery({
    queryKey: ['report-dashboard', deferredFilters],
    queryFn: () => api.getDashboard(deferredFilters),
  })

  const predictionsQuery = useQuery({
    queryKey: ['report-predictions', deferredFilters],
    queryFn: () => api.getPredictions(deferredFilters),
  })

  const dashboard = dashboardQuery.data
  const predictions = predictionsQuery.data

  return (
    <div className="page-stack">
      <section className="hero-panel hero-panel-split">
        <div>
          <p className="eyebrow">US7</p>
          <h2>Exporter un rapport analytique RH en PDF</h2>
          <p className="muted-copy">
            Le rapport reprend les KPI, les visuels clés, la synthèse de corrélation et la distribution des risques sur
            le périmètre filtré.
          </p>
        </div>

        <a className="primary-button link-button" href={getReportUrl(deferredFilters)} target="_blank" rel="noreferrer">
          Télécharger le PDF
        </a>
      </section>

      <FilterBar options={dashboard?.filters} />

      {dashboardQuery.isLoading ? <div className="loading-card">Préparation du rapport...</div> : null}
      {dashboardQuery.isError ? <div className="empty-card">{dashboardQuery.error.message}</div> : null}

      {dashboard ? (
        <>
          <KPIGrid kpis={dashboard.kpis} />
          <section className="detail-card">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Contenu exporté</p>
                <h3>Résumé du futur document</h3>
              </div>
            </div>
            <div className="report-summary">
              <div className="report-summary-item">
                <span>Dataset actif</span>
                <strong>#{dashboard.meta.activeImportId}</strong>
              </div>
              <div className="report-summary-item">
                <span>Population filtrée</span>
                <strong>{dashboard.meta.totalRecords} employés</strong>
              </div>
              <div className="report-summary-item">
                <span>Dernier modèle</span>
                <strong>{dashboard.meta.lastModelTrainedAt ? formatDateTime(dashboard.meta.lastModelTrainedAt) : 'Aucun'}</strong>
              </div>
              <div className="report-summary-item">
                <span>Prédictions incluses</span>
                <strong>{predictions?.items?.length || 0}</strong>
              </div>
            </div>
          </section>
        </>
      ) : null}
    </div>
  )
}
