import { useDeferredValue } from 'react'
import { useQuery } from '@tanstack/react-query'
import { CartesianGrid, Legend, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from 'recharts'

import { ActiveImportNotice } from '../components/ActiveImportNotice'
import { ChartCard } from '../components/ChartCard'
import { CorrelationHeatmap } from '../components/CorrelationHeatmap'
import { FilterBar } from '../components/FilterBar'
import { useGlobalFilters } from '../context/useGlobalFilters'
import { useActiveImport } from '../hooks/useActiveImport'
import { api } from '../lib/api'

function ScatterPanel({ title, data }) {
  const retained = data.filter((item) => item.attrition === 0)
  const attrition = data.filter((item) => item.attrition === 1)

  return (
    <ChartCard title={title}>
      <ResponsiveContainer width="100%" height={320}>
        <ScatterChart>
          <CartesianGrid strokeDasharray="3 3" stroke="#cbd5e1" />
          <XAxis type="number" dataKey="x" stroke="#64748b" />
          <YAxis type="number" dataKey="y" stroke="#64748b" />
          <Tooltip cursor={{ strokeDasharray: '3 3' }} />
          <Legend />
          <Scatter name="Retention" data={retained} fill="#0f766e" />
          <Scatter name="Depart" data={attrition} fill="#f97316" />
        </ScatterChart>
      </ResponsiveContainer>
    </ChartCard>
  )
}

export function AnalyticsPage() {
  const { filters } = useGlobalFilters()
  const deferredFilters = useDeferredValue(filters)
  const importsQuery = useActiveImport()

  const correlationsQuery = useQuery({
    queryKey: ['correlations', deferredFilters],
    queryFn: () => api.getCorrelations(deferredFilters),
    enabled: importsQuery.hasActiveImport,
  })

  const filtersQuery = useQuery({
    queryKey: ['analytics-filter-options'],
    queryFn: api.getFilters,
    enabled: importsQuery.hasActiveImport,
  })

  const correlations = correlationsQuery.data

  return (
    <div className="page-stack">
      <section className="hero-panel">
        <div>
          <p className="eyebrow">US4</p>
          <h2>Explorer les correlations entre formation, performance et retention</h2>
          <p className="muted-copy">
            Passez du KPI a l'explication en observant les liens statistiques entre les variables RH cles.
          </p>
        </div>
      </section>

      {importsQuery.isLoading ? <div className="loading-card">Verification du dataset actif...</div> : null}
      {!importsQuery.isLoading && !importsQuery.hasActiveImport ? <ActiveImportNotice hasImports={importsQuery.hasImports} /> : null}

      {importsQuery.hasActiveImport ? <FilterBar options={filtersQuery.data} /> : null}

      {importsQuery.hasActiveImport && correlationsQuery.isLoading ? <div className="loading-card">Calcul des correlations...</div> : null}
      {importsQuery.hasActiveImport && correlationsQuery.isError ? <div className="empty-card">{correlationsQuery.error.message}</div> : null}

      {importsQuery.hasActiveImport && correlations ? (
        <>
          <ChartCard title="Matrice de correlation" subtitle="Valeurs proches de 1 ou -1 = relation plus forte">
            <CorrelationHeatmap labels={correlations.labels} matrix={correlations.matrix} />
          </ChartCard>

          <div className="insight-list">
            {correlations.insights.map((insight) => (
              <div className="insight-item" key={insight}>
                {insight}
              </div>
            ))}
          </div>

          <div className="chart-grid">
            <ScatterPanel title="Formation vs performance" data={correlations.scatterSeries.trainingVsPerformance} />
            <ScatterPanel title="Satisfaction vs anciennete" data={correlations.scatterSeries.satisfactionVsTenure} />
            <ScatterPanel title="Salaire vs satisfaction" data={correlations.scatterSeries.salaryVsSatisfaction} />
          </div>
        </>
      ) : null}
    </div>
  )
}
