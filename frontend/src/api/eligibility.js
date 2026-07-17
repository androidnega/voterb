import api from './client'
import uploadClient from './uploadClient'
import { uploadQueue } from '@/utils/uploadQueue'

export const eligibilityApi = {
  list(electionUuid) {
    return api.get(`/elections/${electionUuid}/eligibility/`)
  },
  add(electionUuid, data) {
    return api.post(`/elections/${electionUuid}/eligibility/`, data)
  },
  remove(electionUuid, eligibilityUuid) {
    return api.delete(`/elections/${electionUuid}/eligibility/${eligibilityUuid}/`)
  },
  import(electionUuid, file, { registerUuid, categoryUuid } = {}) {
    const formData = new FormData()
    formData.append('file', file)
    if (registerUuid) formData.append('register_uuid', registerUuid)
    if (categoryUuid) formData.append('category_uuid', categoryUuid)
    return uploadQueue.enqueue(
      () => uploadClient.post(`/elections/${electionUuid}/eligibility/import/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }),
      { label: 'voter-import' }
    )
  },
}
