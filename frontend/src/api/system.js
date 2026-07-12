import api from './client'

export const systemApi = {
  getTheme() {
    return api.get('/system/theme/')
  },
  setTheme(theme) {
    return api.patch('/system/theme/', { theme })
  },
}
