import api from './client'

export const dashboardApi = {
  getAdminDashboard() {
    return api.get('/dashboard/admin/')
  },
  getSuperAdminDashboard() {
    return api.get('/dashboard/super-admin/')
  },
}
