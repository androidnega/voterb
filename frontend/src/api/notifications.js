import api from './client'

export const notificationApi = {
  // Get all notifications for the current user
  list() {
    return api.get('/notifications/')
  },
  
  // Mark a single notification as read
  markRead(uuid) {
    return api.post(`/notifications/${uuid}/read/`)
  },
  
  // Mark all notifications as read
  markAllRead() {
    return api.post('/notifications/read-all/')
  }
}
