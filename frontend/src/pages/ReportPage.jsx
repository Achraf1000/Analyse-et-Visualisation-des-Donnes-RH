import { useDeferredValue } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'

import { ActiveImportNotice } from '../components/ActiveImportNotice'
import { FilterBar } from '../components/FilterBar'
import { KPIGrid } from '../components/KPIGrid'
import { useGlobalFilters } from '../context/useGlobalFilters'
import { useActiveImport } from '../hooks/useActiveImport'
import { api } from '../lib/api'
import { formatDateTime } from '../lib/format'

export function ReportPage() {
  const { filters } = useGlobalFilters()
  const deferredFilters = useDeferredValue(filters)
  const importsQuery = useActiveImport()

  const dashboardQuery = useQuery({
    queryKey: ['report-dashboard', deferredFilters],
    queryFn: () => api.getDashboard(deferredFilters),
    enabled: importsQuery.hasActiveImport,
  })

  const reportMutation = useMutation({
    mutationFn: () => api.downloadReport(deferredFilters),
    onSuccess: (blob) => {
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'rapport-rh.pdf'
      link.click()
      URL.revokeObjectURL(url)
    },
  })

  const dashboard = dashboardQuery.data

  return (
    <div className="page-stack">
      <section className="hero-panel hero-panel-split">
        <div>
          <p className="eyebrow">US7</p>
          <h2>Exporter un rapport analytique RH en PDF</h2>
          <p className="muted-copy">
            Le rapport reprend les KPI, les visuels cles, la synthese de correlation et la distribution des risques sur
            le perimetre filtre.
          </p>
        </div>

        {importsQuery.hasActiveImport ? (
          <button
            className="primary-button link-button"
            type="button"
            onClick={() => reportMutation.mutate()}
            disabled={reportMutation.isPending}
          >
            {reportMutation.isPending ? 'Generation...' : 'Telecharger le PDF'}
          </button>
        ) : (
          <button className="primary-button link-button" type="button" disabled>
            PDF indisponible
          </button>
        )}
      </section>

      {importsQuery.isLoading ? <div className="loading-card">Verification du dataset actif...</div> : null}
      {!importsQuery.isLoading && !importsQuery.hasActiveImport ? <ActiveImportNotice hasImports={importsQuery.hasImports} /> : null}

      {importsQuery.hasActiveImport ? <FilterBar options={dashboard?.filters} /> : null}

      {importsQuery.hasActiveImport && dashboardQuery.isLoading ? <div className="loading-card">Preparation du rapport...</div> : null}
      {importsQuery.hasActiveImport && dashboardQuery.isError ? <div className="empty-card">{dashboardQuery.error.message}</div> : null}
      {reportMutation.isError ? <div className="error-banner">{reportMutation.error.message}</div> : null}

      {importsQuery.hasActiveImport && dashboard ? (
        <>
          <KPIGrid kpis={dashboard.kpis} />
          <section className="detail-card">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Contenu exporte</p>
                <h3>Resume du futur document</h3>
              </div>
            </div>
            <div className="report-summary">
              <div className="report-summary-item">
                <span>Dataset actif</span>
                <strong>#{dashboard.meta.activeImportId}</strong>
              </div>
              <div className="report-summary-item">
                <span>Population filtree</span>
                <strong>{dashboard.meta.totalRecords} employes</strong>
              </div>
              <div className="report-summary-item">
                <span>Dernier modele</span>
                <strong>{dashboard.meta.lastModelTrainedAt ? formatDateTime(dashboard.meta.lastModelTrainedAt) : 'Aucun'}</strong>
              </div>
              <div className="report-summary-item">
                <span>Mode export</span>
                <strong>PDF securise</strong>
              </div>
            </div>
          </section>
        </>
      ) : null}
    </div>
  )
}
