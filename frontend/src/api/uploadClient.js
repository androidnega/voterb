import axios from 'axios'

/** Axios client for multipart uploads — longer timeout, no JSON default header */
const uploadClient = axios.create({
  baseURL: '/api/v1',
  timeout: 120000,
})

const NO_REFRESH_PATHS = [
  '/accounts/auth/login/',
  '/accounts/auth/otp/verify/',
  '/accounts/auth/token/refresh/',
  '/accounts/auth/logout/',
]

let refreshPromise = null

uploadClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

uploadClient.interceptors.response.use(
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
        if (!refresh) throw new Error('No refresh token')
        const response = await axios.post('/api/v1/accounts/auth/token/refresh/', { refresh })
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
      return uploadClient(originalRequest)
    } catch {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user_uuid')
      localStorage.removeItem('session_uuid')
      return Promise.reject(error)
    }
  }
)

export default uploadClient
