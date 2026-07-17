import axios from 'axios'
import { API_BASE_URL, apiUrl } from './config'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
})

const NO_AUTH_HEADER_PATHS = [
  '/accounts/auth/login/',
  '/accounts/auth/otp/verify/',
  '/accounts/auth/otp/resend/',
  '/accounts/auth/token/refresh/',
]

const NO_REFRESH_PATHS = [
  ...NO_AUTH_HEADER_PATHS,
  '/accounts/auth/logout/',
]

let refreshPromise = null

function clearSessionTokens() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('user_uuid')
  localStorage.removeItem('session_uuid')
}

function isDefinitiveRefreshFailure(error) {
  const status = error?.response?.status
  // Only wipe tokens when the refresh token itself is rejected.
  return status === 400 || status === 401 || status === 403
}

api.interceptors.request.use((config) => {
  const url = config.url || ''
  const skipAuth = NO_AUTH_HEADER_PATHS.some((path) => url.includes(path))
  if (!skipAuth) {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    const sessionUuid = localStorage.getItem('session_uuid')
    if (sessionUuid) {
      config.headers['X-Session-UUID'] = sessionUuid
    }
  } else if (config.headers) {
    delete config.headers.Authorization
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const url = originalRequest?.url || ''

    if (error.response?.status !== 401 || originalRequest?._retry) {
      return Promise.reject(error)
    }

    if (NO_REFRESH_PATHS.some((path) => url.includes(path))) {
      return Promise.reject(error)
    }

    originalRequest._retry = true

    const storedRefresh = localStorage.getItem('refresh_token')
    if (!storedRefresh) {
      // Keep access token if somehow only refresh is missing — do not wipe
      // the whole session on a single 401 without a refresh attempt.
      return Promise.reject(error)
    }

    if (!refreshPromise) {
      refreshPromise = (async () => {
        const response = await axios.post(
          apiUrl('accounts/auth/token/refresh/'),
          { refresh: storedRefresh },
          { timeout: 10000 },
        )
        const access = response.data.access
        localStorage.setItem('access_token', access)
        return access
      })()
        .catch((refreshError) => {
          if (isDefinitiveRefreshFailure(refreshError)) {
            clearSessionTokens()
          }
          throw refreshError
        })
        .finally(() => {
          refreshPromise = null
        })
    }

    try {
      const access = await refreshPromise
      originalRequest.headers = originalRequest.headers || {}
      originalRequest.headers.Authorization = `Bearer ${access}`
      return api(originalRequest)
    } catch {
      return Promise.reject(error)
    }
  },
)

export default api
