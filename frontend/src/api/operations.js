import api from './client'

export const operationsApi = {
  getOverview() {
    return api.get('/operations/overview/')
  },
  getHealth() {
    return api.get('/operations/health/')
  },
  getInfrastructure() {
    return api.get('/operations/infrastructure/')
  },
  getQueues() {
    return api.get('/operations/queues/')
  },
  getLogs() {
    return api.get('/operations/logs/')
  }
}
