import api from './client'

export const governanceApi = {
  status() {
    return api.get('/accounts/governance/status/')
  },
  listDecisions(params = {}) {
    return api.get('/accounts/governance/decisions/', { params })
  },
  getDecision(uuid) {
    return api.get(`/accounts/governance/decisions/${uuid}/`)
  },
  approve(uuid, note = '') {
    return api.post(`/accounts/governance/decisions/${uuid}/approve/`, { note })
  },
  reject(uuid, reason = '') {
    return api.post(`/accounts/governance/decisions/${uuid}/reject/`, { reason })
  },
  getECStructure() {
    return api.get('/accounts/governance/ec-structure/')
  },
  proposeSubEC(payload) {
    return api.post('/accounts/governance/ec-structure/', payload)
  },
  proposeSubECUpdate(unitUuid, payload) {
    return api.patch(`/accounts/governance/ec-structure/${unitUuid}/`, payload)
  },
}
