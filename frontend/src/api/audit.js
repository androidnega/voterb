import api from './client'

export const auditApi = {
  getMFA() {
    return api.get('/audit/mfa/')
  },
  getAudit(params = {}) {
    return api.get('/audit/audit/', { params })
  },
  getCombined(params = {}) {
    return api.get('/audit/combined/', { params })
  },
  getVoteDetail(auditId) {
    return api.get(`/audit/${auditId}/`)
  },
}
