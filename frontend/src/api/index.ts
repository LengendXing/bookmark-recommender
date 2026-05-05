import request from './request'

export const auth = {
  register: (data: { username: string; email: string; password: string }) => request.post('/auth/register', data),
  login: (data: { username: string; password: string }) => request.post('/auth/login', data),
  me: () => request.get('/auth/me'),
}

export const bookmarks = {
  list: (params: { page?: number; page_size?: number; search?: string } = {}) => request.get('/bookmarks', { params }),
  get: (id: number) => request.get(`/bookmarks/${id}`),
  create: (data: { title: string; url: string; description?: string; author?: string; category?: string; tags?: string[] }) => request.post('/bookmarks', data),
  update: (id: number, data: any) => request.put(`/bookmarks/${id}`, data),
  delete: (id: number) => request.delete(`/bookmarks/${id}`),
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
}

export const recommend = {
  search: (query: string, limit?: number) => request.post('/recommend', { query, limit: limit || 10 }),
  modelStatus: () => request.get('/recommend/model-status'),
  train: (code: string) => request.post('/recommend/train', { code }),
}

export const settings = {
  get: () => request.get('/system-config'),
  update: (data: { api_endpoint?: string; api_key?: string }) => request.put('/system-config', data),
}

export const admin = {
  stats: () => request.get('/admin/stats'),
  auditLogs: (params: { page?: number; page_size?: number; action?: string } = {}) => request.get('/admin/audit-logs', { params }),
  triggerTrain: (code: string) => request.post('/admin/train', { code }),
  deleteBookmark: (id: number, code: string) => request.delete(`/admin/bookmark/${id}`, { data: { code } }),
  kickUser: (id: number, code: string) => request.post(`/admin/user/${id}/kick`, { code }),
}
