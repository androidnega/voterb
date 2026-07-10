import api from './client'

export const dashboardApi = {
  getAdminDashboard() {
    return api.get('/dashboard/admin/')
  }
}
