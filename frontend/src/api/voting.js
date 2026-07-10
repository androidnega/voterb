import api from './client'

export const votingApi = {
  getEligibleElections() {
    return api.get('/voting/eligible/')
  },
  requestSVT(electionUuid) {
    return api.post(`/voting/elections/${electionUuid}/svt/request/`)
  },
  validateSVT(electionUuid, svtCode) {
    return api.post(`/voting/elections/${electionUuid}/svt/validate/`, { svt_code: svtCode })
  },
  getBallot(electionUuid) {
    return api.get(`/voting/elections/${electionUuid}/ballot/`)
  },
  submitVote(electionUuid, selections, svtCode) {
    return api.post(`/voting/elections/${electionUuid}/submit/`, {
      selections,
      svt_code: svtCode
    })
  }
}
