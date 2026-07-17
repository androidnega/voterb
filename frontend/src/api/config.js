export const API_VERSION = 'v1'
export const API_BASE_URL = `/api/${API_VERSION}`

export const apiUrl = (path) =>
  `${API_BASE_URL}/${String(path || '').replace(/^\/+/, '')}`
