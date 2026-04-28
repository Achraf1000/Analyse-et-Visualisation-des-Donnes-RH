const API_ROOT = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')
const TOKEN_STORAGE_KEY = 'rh_auth_token'
let unauthorizedHandler = null

export class ApiError extends Error {
  constructor(message, status, detail) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

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

export function readAuthToken() {
  return window.localStorage.getItem(TOKEN_STORAGE_KEY)
}

export function storeAuthToken(token) {
  window.localStorage.setItem(TOKEN_STORAGE_KEY, token)
}

export function clearAuthToken() {
  window.localStorage.removeItem(TOKEN_STORAGE_KEY)
}

export function setUnauthorizedHandler(handler) {
  unauthorizedHandler = handler
}

async function request(path, options = {}, params) {
  const { skipAuth = false, ...fetchOptions } = options
  const headers = new Headers(fetchOptions.headers || {})
  const token = readAuthToken()

  if (!skipAuth && token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  fetchOptions.headers = headers
  const response = await fetch(buildUrl(path, params), fetchOptions)
  if (!response.ok) {
    let message = 'Une erreur inattendue est survenue.'
    let detail = null
    try {
      const payload = await response.json()
      detail = payload.detail ?? null
      message = typeof payload.detail === 'string' ? payload.detail : message
    } catch {
      message = response.statusText || message
    }
    if (response.status === 401 && !skipAuth) {
      clearAuthToken()
      unauthorizedHandler?.()
    }
    throw new ApiError(message, response.status, detail)
  }

  const contentType = response.headers.get('content-type') || ''
  if (contentType.includes('application/json')) {
    return response.json()
  }
  return response.blob()
}

export function buildFilterParams(filters) {
  const cleanValue = (value) => (value === '' || value === null || value === undefined ? undefined : value)

  return {
    department: cleanValue(filters.department),
    gender: cleanValue(filters.gender),
    tenureMin: cleanValue(filters.tenureMin),
    tenureMax: cleanValue(filters.tenureMax),
    ageMin: cleanValue(filters.ageMin),
    ageMax: cleanValue(filters.ageMax),
  }
}

export function isNoActiveImportError(error) {
  return error instanceof ApiError && error.status === 409
}

export function getReportUrl(filters) {
  return buildUrl('/reports/pdf', buildFilterParams(filters))
}

export const api = {
  login: (credentials) =>
    request(
      '/auth/login',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
        skipAuth: true,
      },
    ),
  me: () => request('/auth/me'),
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
  getFilters: () => request('/filters'),
  getDashboard: (filters) => request('/dashboard', {}, buildFilterParams(filters)),
  getCorrelations: (filters) => request('/analytics/correlations', {}, buildFilterParams(filters)),
  trainAttritionModel: () =>
    request('/models/attrition/train', {
      method: 'POST',
    }),
  getPredictions: (filters) => request('/models/attrition/predictions', {}, buildFilterParams(filters)),
  downloadReport: (filters) => request('/reports/pdf', {}, buildFilterParams(filters)),
}
