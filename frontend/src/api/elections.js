import api from './client'

export const electionApi = {
  // Get all elections
  list() {
    return api.get('/elections/')
  },
  
  // Get single election
  get(uuid) {
    return api.get(`/elections/${uuid}/`)
  },
  
  // Create election
  create(data) {
    return api.post('/elections/', data)
  },
  
  // Update election
  update(uuid, data) {
    return api.put(`/elections/${uuid}/`, data)
  },
  
  // Delete election
  delete(uuid) {
    return api.delete(`/elections/${uuid}/`)
  },
  
  // Open election
  open(uuid) {
    return api.post(`/elections/${uuid}/open/`)
  },
  
  // Close election
  close(uuid) {
    return api.post(`/elections/${uuid}/close/`)
  },
  
  getMonitor(uuid) {
    return api.get(`/elections/${uuid}/monitor/`)
  },

  // Get positions for election
  getPositions(electionUuid) {
    return api.get(`/elections/${electionUuid}/positions/`)
  },
  
  // Create position
  createPosition(electionUuid, data) {
    return api.post(`/elections/${electionUuid}/positions/`, data)
  },

  updatePosition(electionUuid, positionUuid, data) {
    return api.patch(`/elections/${electionUuid}/positions/${positionUuid}/`, data)
  },

  deletePosition(electionUuid, positionUuid) {
    return api.delete(`/elections/${electionUuid}/positions/${positionUuid}/`)
  },
}
