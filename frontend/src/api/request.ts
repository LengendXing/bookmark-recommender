import axios from 'axios'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
})

request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

function parseErrorCode(data: any): number | undefined {
  if (data?.code) return data.code
  if (data?.detail) {
    try { const parsed = typeof data.detail === 'string' ? JSON.parse(data.detail) : data.detail; return parsed.code } catch (_) { /* ignore */ }
  }
  return undefined
}

request.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const status = err.response?.status ?? 0
    const url = err.config?.url ?? '?'
    const method = err.config?.method?.toUpperCase() ?? '?'
    const data = err.response?.data
    console.error(`[API] ${method} ${url} | ${status} |`, data)
    const code = parseErrorCode(data)
    if (code === 1001 || status === 401) {
      if (window.location.pathname !== '/login') {
        localStorage.removeItem('token')
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

export default request
