import axios from 'axios'
import { API_BASE_URL, apiUrl } from './config'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
})

const NO_REFRESH_PATHS = [
  '/accounts/auth/login/',
  '/accounts/auth/otp/verify/',
  '/accounts/auth/token/refresh/',
  '/accounts/auth/logout/',
]

let refreshPromise = null

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const url = originalRequest?.url || ''

    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error)
    }

    if (NO_REFRESH_PATHS.some((path) => url.includes(path))) {
      return Promise.reject(error)
    }

    originalRequest._retry = true

    if (!refreshPromise) {
      refreshPromise = (async () => {
        const refresh = localStorage.getItem('refresh_token')
        if (!refresh) {
          throw new Error('No refresh token')
        }
        const response = await axios.post(apiUrl('accounts/auth/token/refresh/'), { refresh })
        const access = response.data.access
        localStorage.setItem('access_token', access)
        return access
      })().finally(() => {
        refreshPromise = null
      })
    }

    try {
      const access = await refreshPromise
      originalRequest.headers.Authorization = `Bearer ${access}`
      return api(originalRequest)
    } catch {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user_uuid')
      localStorage.removeItem('session_uuid')
      return Promise.reject(error)
    }
  }
)

export default api
