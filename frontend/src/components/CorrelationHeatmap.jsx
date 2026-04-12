export function CorrelationHeatmap({ labels = [], matrix = [] }) {
  if (!labels.length || !matrix.length) {
    return <div className="empty-card">Aucune corrélation calculable.</div>
  }

  return (
    <div className="heatmap-grid" role="table" aria-label="Matrice de corrélation">
      <div className="heatmap-corner" />
      {labels.map((label) => (
        <div key={`column-${label}`} className="heatmap-axis">
          {label}
        </div>
      ))}

      {matrix.map((row, rowIndex) => (
        <div className="heatmap-row" key={labels[rowIndex]}>
          <div className="heatmap-axis heatmap-axis-row">{labels[rowIndex]}</div>
          {row.map((value, columnIndex) => (
            <div
              key={`${rowIndex}-${columnIndex}`}
              className="heatmap-cell"
              style={{
                background: `rgba(13, 148, 136, ${Math.abs(value)})`,
                color: Math.abs(value) > 0.55 ? '#f8fafc' : '#0f172a',
              }}
            >
              {value.toFixed(2)}
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}
