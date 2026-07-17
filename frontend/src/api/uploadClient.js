import axios from 'axios'
import { API_BASE_URL, apiUrl } from './config'

/** Axios client for multipart uploads — longer timeout, no JSON default header */
const uploadClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 min — large register CSV chunks
})

const NO_REFRESH_PATHS = [
  '/accounts/auth/login/',
  '/accounts/auth/otp/verify/',
  '/accounts/auth/token/refresh/',
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
  return status === 400 || status === 401 || status === 403
}

uploadClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  const sessionUuid = localStorage.getItem('session_uuid')
  if (sessionUuid) {
    config.headers['X-Session-UUID'] = sessionUuid
  }
  return config
})

uploadClient.interceptors.response.use(
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
      return uploadClient(originalRequest)
    } catch {
      return Promise.reject(error)
    }
  },
)

export default uploadClient
