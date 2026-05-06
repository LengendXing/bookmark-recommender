import request from './request'

export const auth = {
  register: (data: { username: string; email: string; password: string }) => request.post('/auth/register', data),
  login: (data: { username: string; password: string }) => request.post('/auth/login', data),
  me: () => request.get('/auth/me'),
}

export const bookmarks = {
  list: (params: { page?: number; page_size?: number; search?: string; collection_id?: number } = {}) => request.get('/bookmarks', { params }),
  get: (id: number) => request.get(`/bookmarks/${id}`),
  create: (data: { title: string; url: string; description?: string; author?: string; category?: string; tags?: string[] }) => request.post('/bookmarks', data),
  update: (id: number, data: any) => request.put(`/bookmarks/${id}`, data),
  delete: (id: number) => request.delete(`/bookmarks/${id}`),
  move: (id: number, collectionId: number | null) => request.post(`/bookmarks/${id}/move`, { collection_id: collectionId }),
  ingest: (url: string) => request.post('/bookmarks/ingest', { url }),
  ingestBulk: (urls: string[]) => request.post('/bookmarks/ingest-bulk', { urls }),
  importHtml: (browser: string, file: File) => {
    const formData = new FormData()
    formData.append('browser', browser)
    formData.append('file', file)
    return request.post('/bookmarks/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  export: () => request.get('/bookmarks/export', { responseType: 'blob' }),
  analyzeAll: () => request.post('/bookmarks/analyze-all'),
  analyzeProgress: () => request.get('/bookmarks/analyze-progress'),
}

export const collections = {
  list: () => request.get('/collections'),
  create: (data: { name: string; description?: string }) => request.post('/collections', data),
  update: (id: number, data: { name?: string; description?: string }) => request.put(`/collections/${id}`, data),
  delete: (id: number) => request.delete(`/collections/${id}`),
}

export const recommend = {
  search: (query: string, limit?: number) => request.post('/recommend', { query, limit: limit || 10 }),
  modelStatus: () => request.get('/recommend/model-status'),
  train: (code: string) => request.post('/recommend/train', { code }),
}

export const settings = {
  get: () => request.get('/system-config'),
  update: (data: { api_endpoint?: string; api_key?: string; api_provider?: string; ai_model?: string }) => request.put('/system-config', data),
  test: (data: { api_endpoint: string; api_key: string; api_provider: string; model: string }) => request.post('/system-config/test', data),
  listModels: (data: { api_endpoint: string; api_key: string; api_provider: string; model: string }) => request.post('/system-config/models', data),
}

export const github = {
  listAccounts: () => request.get('/github/accounts'),
  addAccount: (token: string) => request.post('/github/accounts', { token }),
  deleteAccount: (id: number) => request.delete(`/github/accounts/${id}`),
  syncAccount: (id: number) => request.post(`/github/accounts/${id}/sync`),
  listRepos: (params: { q?: string; page?: number; page_size?: number } = {}) => request.get('/github/repos', { params }),
  semanticSearch: (query: string) => request.post('/github/repos/semantic-search', { query }),
  deleteRepo: (id: number) => request.delete(`/github/repos/${id}`),
  importJson: (accountId: number, file: File) => {
    const formData = new FormData()
    formData.append('account_id', String(accountId))
    formData.append('file', file)
    return request.post('/github/repos/import-json', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  exportJson: () => request.get('/github/repos/export', { responseType: 'blob' }),
  analyzeAll: () => request.post('/github/repos/analyze-all'),
  analyzeProgress: () => request.get('/github/repos/analyze-progress'),
  getRepo: (id: number) => request.get(`/github/repos/${id}`),
  generateRecommendations: (data?: { top_k_tags?: number }) => request.post('/github/repos/generate-recommendations', data || {}),
  recommendationsProgress: () => request.get('/github/repos/recommendations-progress'),
  listRecommendations: (params: { page?: number; page_size?: number } = {}) => request.get('/github/repos/recommendations', { params }),
}

export const admin = {
  stats: () => request.get('/admin/stats'),
  auditLogs: (params: { page?: number; page_size?: number; action?: string } = {}) => request.get('/admin/audit-logs', { params }),
  triggerTrain: (code: string) => request.post('/admin/train', { code }),
  deleteBookmark: (id: number, code: string) => request.delete(`/admin/bookmark/${id}`, { data: { code } }),
  kickUser: (id: number, code: string) => request.post(`/admin/user/${id}/kick`, { code }),
}
