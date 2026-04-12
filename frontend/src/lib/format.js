const currencyFormatter = new Intl.NumberFormat('fr-FR', {
  style: 'currency',
  currency: 'EUR',
  maximumFractionDigits: 0,
})

const numberFormatter = new Intl.NumberFormat('fr-FR', {
  maximumFractionDigits: 2,
})

export function formatCurrency(value) {
  return currencyFormatter.format(Number(value || 0))
}

export function formatNumber(value, suffix = '') {
  return `${numberFormatter.format(Number(value || 0))}${suffix}`
}

export function formatPercent(value) {
  return `${numberFormatter.format(Number(value || 0))}%`
}

export function formatDateTime(value) {
  if (!value) {
    return 'N/A'
  }
  return new Intl.DateTimeFormat('fr-FR', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

export function labelizeRisk(value) {
  return {
    low: 'Faible',
    medium: 'Moyen',
    high: 'Élevé',
    non_evalue: 'Non évalué',
  }[value] || value
}
