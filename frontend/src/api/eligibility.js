import api from './client'

export const eligibilityApi = {
  list(electionUuid) {
    return api.get(`/elections/${electionUuid}/eligibility/`)
  },
  add(electionUuid, data) {
    return api.post(`/elections/${electionUuid}/eligibility/`, data)
  },
  remove(electionUuid, eligibilityUuid) {
    return api.delete(`/elections/${electionUuid}/eligibility/${eligibilityUuid}/`)
  },
  import(electionUuid, file) {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/elections/${electionUuid}/eligibility/import/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }
}
