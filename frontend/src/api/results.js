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
  certifyMeta(electionUuid, fingerprint) {
    return api.get(`/results/elections/${electionUuid}/certify/`, {
      headers: fingerprint ? { 'X-Device-Fingerprint': fingerprint } : {},
    })
  },
  certify(electionUuid, payload, fingerprint) {
    return api.post(`/results/elections/${electionUuid}/certify/`, payload, {
      headers: fingerprint ? { 'X-Device-Fingerprint': fingerprint } : {},
    })
  },
  publish(electionUuid) {
    return api.post(`/results/elections/${electionUuid}/publish/`)
  },
  getPublished() {
    return api.get('/results/published/')
  },
  getPublishedDetail(uuid) {
    return api.get(`/results/published/${uuid}/`)
  },
  getLive(electionUuid) {
    return api.get(`/results/elections/${electionUuid}/live/`)
  },
}
