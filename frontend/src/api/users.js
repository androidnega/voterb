import api from './client'

export const usersApi = {
  list(params = {}) {
    return api.get('/accounts/users/', { params })
  },
  get(uuid) {
    return api.get(`/accounts/users/${uuid}/`)
  },
  create(data) {
    return api.post('/accounts/users/', data)
  },
  update(uuid, data) {
    return api.patch(`/accounts/users/${uuid}/`, data)
  },
  delete(uuid) {
    return api.delete(`/accounts/users/${uuid}/`)
  },
  activate(uuid) {
    return api.post(`/accounts/users/${uuid}/activate/`)
  },
  deactivate(uuid) {
    return api.post(`/accounts/users/${uuid}/deactivate/`)
  },
  resetPassword(uuid, password) {
    return api.post(`/accounts/users/${uuid}/reset-password/`, { password })
  },
  getRoles() {
    return api.get('/accounts/roles/')
  }
}
