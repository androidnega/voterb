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
  listFeatureFlags() {
    return api.get('/system/feature-flags/')
  },
  updateFeatureFlag(key, isEnabled) {
    return api.patch(`/system/feature-flags/${key}/`, { is_enabled: isEnabled })
  },
  getInstitution() {
    return api.get('/system/institution/')
  },
  getMaintenance() {
    return api.get('/system/maintenance/')
  },
  setMaintenance(payload) {
    return api.put('/system/maintenance/', payload)
  },
}
