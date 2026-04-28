import { formatCurrency, formatNumber, formatPercent } from '../lib/format'

const kpiConfig = [
  { key: 'headcount', label: 'Effectif', formatter: (value) => formatNumber(value) },
  { key: 'turnoverRate', label: 'Turnover', formatter: (value) => formatPercent(value) },
  { key: 'averageTenure', label: 'Ancienneté moyenne', formatter: (value) => formatNumber(value, ' ans') },
  { key: 'averageSalary', label: 'Salaire moyen', formatter: (value) => formatCurrency(value) },
  { key: 'totalCost', label: 'Coût RH total', formatter: (value) => formatCurrency(value) },
]

export function KPIGrid({ kpis }) {
  return (
    <section className="kpi-grid">
      {kpiConfig.map((item) => (
        <article className="kpi-card" key={item.key}>
          <span>{item.label}</span>
          <strong>{item.formatter(kpis?.[item.key])}</strong>
        </article>
      ))}
    </section>
  )
}
