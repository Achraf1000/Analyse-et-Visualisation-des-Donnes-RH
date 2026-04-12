const API_ROOT = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')

function buildUrl(path, params) {
  const prefix = path.startsWith('/api') ? '' : '/api'
  const url = new URL(`${API_ROOT}${prefix}${path}`, window.location.origin)
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.set(key, value)
      }
    })
  }
  return API_ROOT ? `${url.pathname}${url.search}`.replace(/^/, API_ROOT) : `${url.pathname}${url.search}`
}

async function request(path, options = {}, params) {
  const response = await fetch(buildUrl(path, params), options)
  if (!response.ok) {
    let message = 'Une erreur inattendue est survenue.'
    try {
      const payload = await response.json()
      message = payload.detail || message
    } catch {
      message = response.statusText || message
    }
    throw new Error(message)
  }

  const contentType = response.headers.get('content-type') || ''
  if (contentType.includes('application/json')) {
    return response.json()
  }
  return response.blob()
}

export function buildFilterParams(filters) {
  return {
    department: filters.department || undefined,
    gender: filters.gender || undefined,
    tenureMin: filters.tenureMin || undefined,
    tenureMax: filters.tenureMax || undefined,
    ageMin: filters.ageMin || undefined,
    ageMax: filters.ageMax || undefined,
  }
}

export function getReportUrl(filters) {
  return buildUrl('/reports/pdf', buildFilterParams(filters))
}

export const api = {
  listImports: () => request('/imports'),
  getImport: (importId) => request(`/imports/${importId}`),
  getImportIssues: (importId, page = 1, pageSize = 25) =>
    request(`/imports/${importId}/issues`, {}, { page, pageSize }),
  uploadCsv: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return request('/imports/csv', {
      method: 'POST',
      body: formData,
    })
  },
  patchRecord: (importId, recordId, payload) =>
    request(`/imports/${importId}/records/${recordId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  activateImport: (importId) =>
    request(`/imports/${importId}/activate`, {
      method: 'POST',
    }),
  getDashboard: (filters) => request('/dashboard', {}, buildFilterParams(filters)),
  getCorrelations: (filters) => request('/analytics/correlations', {}, buildFilterParams(filters)),
  trainAttritionModel: () =>
    request('/models/attrition/train', {
      method: 'POST',
    }),
  getPredictions: (filters) => request('/models/attrition/predictions', {}, buildFilterParams(filters)),
}
