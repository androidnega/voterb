import api from './client'

export const systemApi = {
  getTheme() {
    return api.get('/system/theme/')
  },
  setTheme(themeOrPayload) {
    const payload = typeof themeOrPayload === 'string'
      ? { theme: themeOrPayload }
      : themeOrPayload
    return api.patch('/system/theme/', payload)
  },
}
