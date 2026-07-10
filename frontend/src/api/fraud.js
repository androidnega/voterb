import api from './client'

export const fraudApi = {
  // Stats
  getStats() {
    return api.get('/fraud/stats/')
  },
  
  // Alerts
  listAlerts() {
    return api.get('/fraud/alerts/')
  },
  getAlert(uuid) {
    return api.get(`/fraud/alerts/${uuid}/`)
  },
  resolveAlert(uuid) {
    return api.post(`/fraud/alerts/${uuid}/resolve/`)
  },
  escalateAlert(uuid) {
    return api.post(`/fraud/alerts/${uuid}/escalate/`)
  },
  
  // Cases
  listCases() {
    return api.get('/fraud/cases/')
  },
  getCase(uuid) {
    return api.get(`/fraud/cases/${uuid}/`)
  },
  addNote(uuid, note) {
    return api.post(`/fraud/cases/${uuid}/note/`, { note })
  },
  resolveCase(uuid) {
    return api.post(`/fraud/cases/${uuid}/resolve/`)
  }
}
