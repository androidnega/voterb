import api from './client'

export const resultsApi = {
  list() {
    return api.get('/results/elections/')
  },
  getCertificationQueue() {
    return api.get('/results/certification-queue/')
  },
  generate(electionUuid) {
    return api.post(`/results/elections/${electionUuid}/generate/`)
  },
  preview(electionUuid) {
    return api.get(`/results/elections/${electionUuid}/preview/`)
  },
  certify(electionUuid) {
    return api.post(`/results/elections/${electionUuid}/certify/`)
  },
  publish(electionUuid) {
    return api.post(`/results/elections/${electionUuid}/publish/`)
  },
  getPublished() {
    return api.get('/results/published/')
  },
  getPublishedDetail(uuid) {
    return api.get(`/results/published/${uuid}/`)
  }
}
