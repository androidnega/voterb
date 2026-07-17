import api from './client'

export const academicApi = {
  faculties(params = {}) {
    return api.get('/elections/faculties/', { params })
  },
  createFaculty(data) {
    return api.post('/elections/faculties/create/', data)
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
    return api.post('/elections/departments/create/', data)
  },
  updateDepartment(uuid, data) {
    return api.patch(`/elections/departments/${uuid}/`, data)
  },
  deleteDepartment(uuid) {
    return api.delete(`/elections/departments/${uuid}/`)
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
