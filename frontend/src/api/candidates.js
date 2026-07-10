import api from './client'

export const candidateApi = {
  // Get candidates for an election
  list(electionUuid) {
    return api.get(`/elections/${electionUuid}/candidates/`)
  },
  
  // Get candidates for a specific position
  listByPosition(electionUuid, positionUuid) {
    return api.get(`/elections/${electionUuid}/positions/${positionUuid}/candidates/`)
  },
  
  // Create candidate
  create(electionUuid, data) {
    return api.post(`/elections/${electionUuid}/candidates/`, data)
  },
  
  // Update candidate
  update(electionUuid, candidateUuid, data) {
    return api.put(`/elections/${electionUuid}/candidates/${candidateUuid}/`, data)
  },
  
  // Approve candidate
  approve(electionUuid, candidateUuid) {
    return api.post(`/elections/${electionUuid}/candidates/${candidateUuid}/approve/`)
  },
  
  // Reject candidate
  reject(electionUuid, candidateUuid) {
    return api.post(`/elections/${electionUuid}/candidates/${candidateUuid}/reject/`)
  },
  
  // Delete candidate
  delete(electionUuid, candidateUuid) {
    return api.delete(`/elections/${electionUuid}/candidates/${candidateUuid}/`)
  }
}
