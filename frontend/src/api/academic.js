import api from './client'

export const academicApi = {
  faculties(params = {}) {
    return api.get('/elections/faculties/', { params })
  },
  createFaculty(data) {
    return api.post('/elections/faculties/', data)
  },
  updateFaculty(uuid, data) {
    return api.patch(`/elections/faculties/${uuid}/`, data)
  },
  deleteFaculty(uuid) {
    return api.delete(`/elections/faculties/${uuid}/`)
  },

  departments(params = {}) {
    return api.get('/elections/departments/', { params })
  },
  createDepartment(data) {
    return api.post('/elections/departments/', data)
  },
  updateDepartment(uuid, data) {
    return api.patch(`/elections/departments/${uuid}/`, data)
  },
  deleteDepartment(uuid) {
    return api.delete(`/elections/departments/${uuid}/`)
  },

  levels() {
    return api.get('/elections/levels/')
  },
  createLevel(data) {
    return api.post('/elections/levels/', data)
  },
  updateLevel(uuid, data) {
    return api.patch(`/elections/levels/${uuid}/`, data)
  },
  deleteLevel(uuid) {
    return api.delete(`/elections/levels/${uuid}/`)
  },
}

export const onboardingApi = {
  getOptions() {
    return api.get('/accounts/onboarding/options/')
  },
  complete(data) {
    return api.post('/accounts/onboarding/', data)
  },
}
