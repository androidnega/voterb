import api from './client'

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
  getBallot(electionUuid) {
    return api.get(`/voting/elections/${electionUuid}/ballot/`)
  },
  submitVote(electionUuid, selections, svtCode) {
    const payload = { selections }
    if (svtCode) payload.svt_code = svtCode
    return api.post(`/voting/elections/${electionUuid}/submit/`, payload)
  },
}
