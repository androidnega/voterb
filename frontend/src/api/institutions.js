import api from './client'

export const institutionApi = {
  list() {
    return api.get('/system/institutions/')
  },
  mine() {
    return api.get('/system/institutions/mine/')
  },
  get(uuid) {
    return api.get(`/system/institutions/${uuid}/`)
  },
  create(payload) {
    return api.post('/system/institutions/', payload)
  },
  update(uuid, payload) {
    return api.patch(`/system/institutions/${uuid}/`, payload)
  },
  createMainEC(institutionUuid, payload) {
    return api.post(`/system/institutions/${institutionUuid}/main-ec/`, payload)
  },
}
