import api from './client'

export const strongroomApi = {
  // List elections with strongroom data
  list() {
    return api.get('/strongroom/elections/')
  },
  // Get strongroom details for an election
  detail(uuid) {
    return api.get(`/strongroom/elections/${uuid}/`)
  },
  // Lock election
  lock(uuid) {
    return api.post(`/strongroom/elections/${uuid}/lock/`)
  },
  // Public verification (no auth)
  verifySeal(sealHash) {
    return api.post('/strongroom/public/verify/', { seal_hash: sealHash })
  }
}
