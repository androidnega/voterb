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
  import(electionUuid, file) {
    const formData = new FormData()
    formData.append('file', file)
    return uploadQueue.enqueue(
      () => uploadClient.post(`/elections/${electionUuid}/eligibility/import/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }),
      { label: 'voter-import' }
    )
  },
}
