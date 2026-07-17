import api from './client'
import uploadClient from './uploadClient'
import { uploadQueue } from '@/utils/uploadQueue'

/** Institutional registers owned by Main EC (architecture: TTU REGISTER). */
export const institutionRegisterApi = {
  list() {
    return api.get('/elections/institution-registers/')
  },
  /**
   * Create register + faculty/department category in one call.
   * @param {{ name: string, description?: string, faculty_uuid?: string, department_uuid?: string }} data
   */
  create(data) {
    return api.post('/elections/institution-registers/', data)
  },
  get(registerUuid) {
    return api.get(`/elections/institution-registers/${registerUuid}/`)
  },
  update(registerUuid, data) {
    return api.patch(`/elections/institution-registers/${registerUuid}/`, data)
  },
  remove(registerUuid) {
    return api.delete(`/elections/institution-registers/${registerUuid}/`)
  },
  listCategories(registerUuid) {
    return api.get(`/elections/institution-registers/${registerUuid}/categories/`)
  },
  assignCategory(registerUuid, data) {
    return api.post(`/elections/institution-registers/${registerUuid}/categories/`, data)
  },
  removeCategory(registerUuid, categoryUuid) {
    return api.delete(
      `/elections/institution-registers/${registerUuid}/categories/${categoryUuid}/`,
    )
  },
  listEntries(registerUuid, params = {}) {
    return api.get(`/elections/institution-registers/${registerUuid}/entries/`, { params })
  },
  /**
   * Propose voter edit (dual Main EC approval).
   */
  updateEntry(registerUuid, entryUuid, data) {
    return api.patch(`/elections/institution-registers/${registerUuid}/entries/${entryUuid}/`, data)
  },
  /**
   * Import one CSV chunk (queued). Supports upload progress callback.
   */
  importCsv(registerUuid, { categoryUuid, file, fileName, onUploadProgress }) {
    const formData = new FormData()
    formData.append('category_uuid', categoryUuid)
    formData.append('file', file, fileName || file.name || 'register.csv')
    return uploadQueue.enqueue(
      () => uploadClient.post(
        `/elections/institution-registers/${registerUuid}/import/`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (event) => {
            if (typeof onUploadProgress === 'function' && event.total) {
              onUploadProgress(Math.round((event.loaded / event.total) * 100))
            }
          },
        },
      ),
      { label: 'institution-register-import' },
    )
  },
  /**
   * Start dual-approved re-upload (staging). Then importCsv into staging_uuid.
   */
  startReplace(registerUuid, { categoryUuid }) {
    return api.post(`/elections/institution-registers/${registerUuid}/replace/`, {
      category_uuid: categoryUuid,
    })
  },
}

export const registerApi = {
  available() {
    return api.get('/elections/registers/available/')
  },
  list(electionUuid) {
    return api.get(`/elections/${electionUuid}/registers/`)
  },
  create(electionUuid, data) {
    return api.post(`/elections/${electionUuid}/registers/`, data)
  },
  get(electionUuid, registerUuid) {
    return api.get(`/elections/${electionUuid}/registers/${registerUuid}/`)
  },
  update(electionUuid, registerUuid, data) {
    return api.patch(`/elections/${electionUuid}/registers/${registerUuid}/`, data)
  },
  remove(electionUuid, registerUuid) {
    return api.delete(`/elections/${electionUuid}/registers/${registerUuid}/`)
  },
  listCategories(electionUuid, registerUuid) {
    return api.get(`/elections/${electionUuid}/registers/${registerUuid}/categories/`)
  },
  createCategory(electionUuid, registerUuid, data) {
    return api.post(`/elections/${electionUuid}/registers/${registerUuid}/categories/`, data)
  },
  updateCategory(electionUuid, registerUuid, categoryUuid, data) {
    return api.patch(
      `/elections/${electionUuid}/registers/${registerUuid}/categories/${categoryUuid}/`,
      data,
    )
  },
  removeCategory(electionUuid, registerUuid, categoryUuid) {
    return api.delete(
      `/elections/${electionUuid}/registers/${registerUuid}/categories/${categoryUuid}/`,
    )
  },
  listEntries(electionUuid, registerUuid, params = {}) {
    return api.get(`/elections/${electionUuid}/registers/${registerUuid}/entries/`, { params })
  },
  importCsv(electionUuid, registerUuid, { categoryUuid, file }) {
    const formData = new FormData()
    formData.append('category_uuid', categoryUuid)
    formData.append('file', file)
    return uploadQueue.enqueue(
      () => uploadClient.post(
        `/elections/${electionUuid}/registers/${registerUuid}/import/`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } },
      ),
      { label: 'register-import' },
    )
  },
}
