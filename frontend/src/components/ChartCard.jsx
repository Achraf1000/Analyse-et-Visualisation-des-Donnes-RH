export function ChartCard({ title, subtitle, children }) {
  return (
    <section className="chart-card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Analyse</p>
          <h3>{title}</h3>
        </div>
        {subtitle ? <span className="muted-copy">{subtitle}</span> : null}
      </div>
      <div className="chart-wrapper">{children}</div>
    </section>
  )
}
