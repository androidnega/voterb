import api from './client'

export const auditApi = {
  // Get MFA logs
  getMFA() {
    return api.get('/audit/mfa/')
  },
  // Get audit logs
  getAudit() {
    return api.get('/audit/audit/')
  },
  // Combined logs with filters
  getCombined(params = {}) {
    return api.get('/audit/combined/', { params })
  }
}
