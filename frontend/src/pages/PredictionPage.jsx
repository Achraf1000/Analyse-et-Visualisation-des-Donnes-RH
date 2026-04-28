import { useDeferredValue } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { ActiveImportNotice } from '../components/ActiveImportNotice'
import { ChartCard } from '../components/ChartCard'
import { DataTable } from '../components/DataTable'
import { FilterBar } from '../components/FilterBar'
import { useGlobalFilters } from '../context/useGlobalFilters'
import { useActiveImport } from '../hooks/useActiveImport'
import { api } from '../lib/api'
import { formatCurrency, formatDateTime, formatPercent, labelizeRisk } from '../lib/format'

const riskColors = {
  low: '#22c55e',
  medium: '#f59e0b',
  high: '#ef4444',
  non_evalue: '#94a3b8',
}

export function PredictionPage() {
  const queryClient = useQueryClient()
  const { filters } = useGlobalFilters()
  const deferredFilters = useDeferredValue(filters)
  const importsQuery = useActiveImport()

  const dashboardQuery = useQuery({
    queryKey: ['prediction-dashboard-options', deferredFilters],
    queryFn: () => api.getDashboard(deferredFilters),
    enabled: importsQuery.hasActiveImport,
  })

  const predictionsQuery = useQuery({
    queryKey: ['predictions', deferredFilters],
    queryFn: () => api.getPredictions(deferredFilters),
    enabled: importsQuery.hasActiveImport,
  })

  const trainMutation = useMutation({
    mutationFn: api.trainAttritionModel,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['predictions'] })
      await queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })

  const predictions = predictionsQuery.data
  const topRiskData =
    predictions?.items?.slice(0, 8).map((item) => ({
      name: item.fullName || item.employeeId,
      value: Number((item.riskProbability * 100).toFixed(2)),
      riskLevel: item.riskLevel,
    })) || []

  const predictionColumns = [
    {
      accessorKey: 'employeeId',
      header: 'Employe',
      cell: ({ row }) => (
        <div>
          <strong>{row.original.fullName || row.original.employeeId}</strong>
          <div className="muted-copy">{row.original.department}</div>
        </div>
      ),
    },
    {
      accessorKey: 'tenureYears',
      header: 'Anciennete',
      cell: ({ getValue }) => `${getValue() || 0} ans`,
    },
    {
      accessorKey: 'satisfactionScore',
      header: 'Satisfaction',
    },
    {
      accessorKey: 'salary',
      header: 'Salaire',
      cell: ({ getValue }) => formatCurrency(getValue()),
    },
    {
      accessorKey: 'riskProbability',
      header: 'Probabilite',
      cell: ({ getValue }) => formatPercent(Number((getValue() || 0) * 100).toFixed(2)),
    },
    {
      accessorKey: 'riskLevel',
      header: 'Niveau',
      cell: ({ getValue }) => <span className={`status-pill risk-${getValue()}`}>{labelizeRisk(getValue())}</span>,
    },
  ]

  return (
    <div className="page-stack">
      <section className="hero-panel hero-panel-split">
        <div>
          <p className="eyebrow">US5</p>
          <h2>Predire le risque de depart des employes</h2>
          <p className="muted-copy">
            Entrainez un modele de regression logistique interpretable, inspectez ses metriques et priorisez les cas a
            risque.
          </p>
        </div>

        <div className="cta-cluster">
          <button
            className="primary-button"
            type="button"
            onClick={() => trainMutation.mutate()}
            disabled={!importsQuery.hasActiveImport || trainMutation.isPending}
          >
            {trainMutation.isPending ? 'Entrainement...' : "Lancer l'entrainement"}
          </button>
          {trainMutation.isError ? <span className="error-text">{trainMutation.error.message}</span> : null}
        </div>
      </section>

      {importsQuery.isLoading ? <div className="loading-card">Verification du dataset actif...</div> : null}
      {!importsQuery.isLoading && !importsQuery.hasActiveImport ? <ActiveImportNotice hasImports={importsQuery.hasImports} /> : null}

      {importsQuery.hasActiveImport ? <FilterBar options={dashboardQuery.data?.filters} /> : null}

      {importsQuery.hasActiveImport && predictionsQuery.isLoading ? <div className="loading-card">Calcul des predictions...</div> : null}
      {importsQuery.hasActiveImport && predictionsQuery.isError ? <div className="empty-card">{predictionsQuery.error.message}</div> : null}

      {importsQuery.hasActiveImport && predictions?.modelRun ? (
        <>
          <div className="summary-grid">
            <article className="summary-card">
              <span>Accuracy</span>
              <strong>{formatPercent(predictions.modelRun.metrics.accuracy * 100)}</strong>
            </article>
            <article className="summary-card">
              <span>Precision</span>
              <strong>{formatPercent(predictions.modelRun.metrics.precision * 100)}</strong>
            </article>
            <article className="summary-card">
              <span>Recall</span>
              <strong>{formatPercent(predictions.modelRun.metrics.recall * 100)}</strong>
            </article>
            <article className="summary-card">
              <span>ROC-AUC</span>
              <strong>{formatPercent(predictions.modelRun.metrics.rocAuc * 100)}</strong>
            </article>
          </div>

          <div className="chart-grid chart-grid-wide">
            <ChartCard title="Top employes a risque">
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={topRiskData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#cbd5e1" />
                  <XAxis dataKey="name" stroke="#64748b" />
                  <YAxis stroke="#64748b" />
                  <Tooltip />
                  <Bar dataKey="value" radius={[10, 10, 0, 0]}>
                    {topRiskData.map((item) => (
                      <Cell key={item.name} fill={riskColors[item.riskLevel]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Dernier entrainement" subtitle={`Execute le ${formatDateTime(predictions.modelRun.trainedAt)}`}>
              <div className="confusion-grid">
                {predictions.modelRun.confusionMatrix.map((row, rowIndex) =>
                  row.map((value, cellIndex) => (
                    <div className="confusion-cell" key={`${rowIndex}-${cellIndex}`}>
                      <span>
                        {rowIndex === 0 ? 'Reel 0' : 'Reel 1'} · {cellIndex === 0 ? 'Predit 0' : 'Predit 1'}
                      </span>
                      <strong>{value}</strong>
                    </div>
                  )),
                )}
              </div>
            </ChartCard>

            <ChartCard title="Variables les plus influentes">
              <div className="coefficient-list">
                {predictions.modelRun.coefficients.map((coefficient) => (
                  <div className="coefficient-row" key={coefficient.feature}>
                    <span>{coefficient.feature}</span>
                    <strong>{coefficient.coefficient}</strong>
                  </div>
                ))}
              </div>
            </ChartCard>
          </div>
        </>
      ) : null}

      {importsQuery.hasActiveImport && predictions && !predictions.modelRun ? (
        <div className="empty-card">
          Aucun modele entraine pour le dataset actif. Lancez un entrainement pour afficher les probabilites de depart.
        </div>
      ) : null}

      {importsQuery.hasActiveImport ? (
        <ChartCard title="Probabilites de depart par employe" subtitle="Donnees filtrees selon le perimetre global">
          <DataTable data={predictions?.items || []} columns={predictionColumns} emptyMessage="Aucune prediction disponible." />
        </ChartCard>
      ) : null}
    </div>
  )
}
