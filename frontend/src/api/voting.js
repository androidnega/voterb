import api from './client'
import uploadClient from './uploadClient'

export const votingApi = {
  getEligibleElections() {
    return api.get('/voting/eligible/')
  },
  requestSVT(electionUuid, options = {}) {
    return api.post(`/voting/elections/${electionUuid}/svt/request/`, options)
  },
  validateSVT(electionUuid, svtCode) {
    return api.post(`/voting/elections/${electionUuid}/svt/validate/`, { svt_code: svtCode })
  },
  getSvtSession(electionUuid) {
    return api.get(`/voting/elections/${electionUuid}/svt/session/`)
  },
  getPresence(electionUuid) {
    return api.get(`/voting/elections/${electionUuid}/presence/`)
  },
  uploadPresence(electionUuid, imageBlob, filename = 'presence.jpg') {
    const formData = new FormData()
    formData.append('image', imageBlob, filename)
    return uploadClient.post(`/voting/elections/${electionUuid}/presence/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  getBallot(electionUuid) {
    return api.get(`/voting/elections/${electionUuid}/ballot/`)
  },
  submitVote(electionUuid, selections, svtCode, clientContext) {
    const payload = { selections }
    if (svtCode) payload.svt_code = svtCode
    if (clientContext) payload.client_context = clientContext
    return api.post(`/voting/elections/${electionUuid}/submit/`, payload)
  },
  clearStudentVote(electionUuid, userUuid) {
    return api.post(`/voting/elections/${electionUuid}/voters/${userUuid}/clear/`)
  },
}
