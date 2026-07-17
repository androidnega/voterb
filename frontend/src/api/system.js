import api from './client'
import uploadClient from './uploadClient'

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
  listSettings(category) {
    return api.get('/system/settings/', { params: category ? { category } : undefined })
  },
  updateSetting(key, value) {
    return api.patch(`/system/settings/${key}/`, { value: String(value) })
  },
  getInstitution() {
    return api.get('/system/institution/')
  },
  updateInstitution(payload) {
    return api.put('/system/institution/', payload)
  },
  updateInstitutionLogo(file, fields = {}) {
    const formData = new FormData()
    Object.entries(fields).forEach(([key, value]) => {
      if (value != null && value !== '') formData.append(key, String(value))
    })
    if (file) formData.append('logo', file)
    return uploadClient.put('/system/institution/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  getMaintenance() {
    return api.get('/system/maintenance/')
  },
  setMaintenance(payload) {
    return api.put('/system/maintenance/', payload)
  },
}
