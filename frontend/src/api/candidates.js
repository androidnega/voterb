import api from './client'
import uploadClient from './uploadClient'
import { uploadQueue } from '@/utils/uploadQueue'

function buildCandidateFormData(data, photoFile) {
  const formData = new FormData()
  if (data.position_uuid) formData.append('position_uuid', data.position_uuid)
  if (data.full_name) formData.append('full_name', data.full_name)
  if (data.faculty_uuid) formData.append('faculty_uuid', data.faculty_uuid)
  if (data.department_uuid) formData.append('department_uuid', data.department_uuid)
  if (data.department) formData.append('department', data.department)
  if (data.manifesto) formData.append('manifesto', data.manifesto)
  if (data.ballot_number != null && data.ballot_number !== '') {
    formData.append('ballot_number', String(data.ballot_number))
  }
  if (photoFile) formData.append('photo', photoFile)
  return formData
}

export const candidateApi = {
  list(electionUuid) {
    return api.get(`/elections/${electionUuid}/candidates/`)
  },

  listByPosition(electionUuid, positionUuid) {
    return api.get(`/elections/${electionUuid}/positions/${positionUuid}/candidates/`)
  },

  create(electionUuid, data, photoFile = null) {
    if (photoFile) {
      const formData = buildCandidateFormData(data, photoFile)
      return uploadQueue.enqueue(
        () => uploadClient.post(`/elections/${electionUuid}/candidates/`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        }),
        { label: 'candidate-create' }
      )
    }
    return api.post(`/elections/${electionUuid}/candidates/`, data)
  },

  updatePhoto(electionUuid, candidateUuid, photoFile) {
    const formData = new FormData()
    formData.append('photo', photoFile)
    return uploadQueue.enqueue(
      () => uploadClient.patch(`/elections/${electionUuid}/candidates/${candidateUuid}/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }),
      { label: 'candidate-photo' }
    )
  },

  update(electionUuid, candidateUuid, data) {
    return api.put(`/elections/${electionUuid}/candidates/${candidateUuid}/`, data)
  },

  approve(electionUuid, candidateUuid) {
    return api.post(`/elections/${electionUuid}/candidates/${candidateUuid}/approve/`)
  },

  reject(electionUuid, candidateUuid) {
    return api.post(`/elections/${electionUuid}/candidates/${candidateUuid}/reject/`)
  },

  delete(electionUuid, candidateUuid) {
    return api.delete(`/elections/${electionUuid}/candidates/${candidateUuid}/`)
  },
}
