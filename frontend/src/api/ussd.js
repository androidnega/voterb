import api from './client'

export const ussdApi = {
  getStats() {
    return api.get('/ussd/stats/')
  },
  listSessions() {
    return api.get('/ussd/sessions/')
  },
  getSession(uuid) {
    return api.get(`/ussd/sessions/${uuid}/`)
  },
  getSessionLogs(sessionUuid) {
    return api.get(`/ussd/sessions/${sessionUuid}/logs/`)
  }
}
