import { useDeferredValue } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { ActiveImportNotice } from '../components/ActiveImportNotice'
import { ChartCard } from '../components/ChartCard'
import { FilterBar } from '../components/FilterBar'
import { KPIGrid } from '../components/KPIGrid'
import { useGlobalFilters } from '../context/useGlobalFilters'
import { useActiveImport } from '../hooks/useActiveImport'
import { api } from '../lib/api'

const palette = ['#0f766e', '#f97316', '#0f172a', '#14b8a6', '#facc15']

export function DashboardPage() {
  const { filters } = useGlobalFilters()
  const deferredFilters = useDeferredValue(filters)
  const importsQuery = useActiveImport()

  const dashboardQuery = useQuery({
    queryKey: ['dashboard', deferredFilters],
    queryFn: () => api.getDashboard(deferredFilters),
    enabled: importsQuery.hasActiveImport,
  })

  const dashboard = dashboardQuery.data

  return (
    <div className="page-stack">
      <section className="hero-panel">
        <div>
          <p className="eyebrow">Pilotage RH</p>
          <h2>Vue synthetique des indicateurs cles</h2>
          <p className="muted-copy">
            Les KPI et graphiques se recalculent automatiquement a partir du dataset actif et des filtres globaux.
          </p>
        </div>
      </section>

      {importsQuery.isLoading ? <div className="loading-card">Verification du dataset actif...</div> : null}
      {!importsQuery.isLoading && !importsQuery.hasActiveImport ? <ActiveImportNotice hasImports={importsQuery.hasImports} /> : null}

      {importsQuery.hasActiveImport ? <FilterBar options={dashboard?.filters} /> : null}

      {importsQuery.hasActiveImport && dashboardQuery.isLoading ? <div className="loading-card">Chargement du tableau de bord...</div> : null}
      {importsQuery.hasActiveImport && dashboardQuery.isError ? <div className="empty-card">{dashboardQuery.error.message}</div> : null}

      {importsQuery.hasActiveImport && dashboard ? (
        <>
          <KPIGrid kpis={dashboard.kpis} />

          <div className="chart-grid chart-grid-wide">
            <ChartCard title="Effectif et turnover par departement" subtitle="Barres: effectif, ligne: turnover">
              <ResponsiveContainer width="100%" height={320}>
                <ComposedChart data={dashboard.charts.departmentHeadcount}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#cbd5e1" />
                  <XAxis dataKey="name" stroke="#64748b" />
                  <YAxis yAxisId="left" stroke="#64748b" />
                  <YAxis yAxisId="right" orientation="right" stroke="#f97316" />
                  <Tooltip />
                  <Legend />
                  <Bar yAxisId="left" dataKey="value" name="Effectif" fill="#0f766e" radius={[10, 10, 0, 0]} />
                  <Line yAxisId="right" type="monotone" dataKey="secondaryValue" name="Turnover %" stroke="#f97316" strokeWidth={3} />
                </ComposedChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Repartition par sexe">
              <ResponsiveContainer width="100%" height={320}>
                <PieChart>
                  <Pie data={dashboard.charts.genderDistribution} dataKey="value" nameKey="name" innerRadius={70} outerRadius={100}>
                    {dashboard.charts.genderDistribution.map((entry, index) => (
                      <Cell key={entry.name} fill={palette[index % palette.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Distribution de l'anciennete">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={dashboard.charts.tenureDistribution}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#cbd5e1" />
                  <XAxis dataKey="name" stroke="#64748b" />
                  <YAxis stroke="#64748b" />
                  <Tooltip />
                  <Bar dataKey="value" fill="#0f172a" radius={[10, 10, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Distribution des risques predits">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={dashboard.charts.riskDistribution}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#cbd5e1" />
                  <XAxis dataKey="name" stroke="#64748b" />
                  <YAxis stroke="#64748b" />
                  <Tooltip />
                  <Bar dataKey="value" radius={[10, 10, 0, 0]}>
                    {dashboard.charts.riskDistribution.map((entry, index) => (
                      <Cell key={entry.name} fill={palette[index % palette.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>
        </>
      ) : null}
    </div>
  )
}
