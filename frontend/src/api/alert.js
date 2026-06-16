import api from './index'

export const alertApi = {
  getAlertConfigs(params) {
    return api.get('/alerts/configs', { params })
  },
  createAlertConfig(data) {
    return api.post('/alerts/configs', data)
  },
  updateAlertConfig(id, data) {
    return api.put(`/alerts/configs/${id}`, data)
  },
  deleteAlertConfig(id) {
    return api.delete(`/alerts/configs/${id}`)
  },
  getAlertRecords(params) {
    return api.get('/alerts', { params })
  },
  markAsRead(id) {
    return api.put(`/alerts/${id}/read`)
  },
  markAllAsRead() {
    return api.put('/alerts/read-all')
  },
  deleteAlertRecord(id) {
    return api.delete(`/alerts/${id}`)
  },
  getFeedbacks(params) {
    return api.get('/alerts/feedbacks', { params })
  },
  createFeedback(data) {
    return api.post('/alerts/feedbacks', data)
  },
  updateFeedback(id, data) {
    return api.put(`/alerts/feedbacks/${id}`, data)
  },
  deleteFeedback(id) {
    return api.delete(`/alerts/feedbacks/${id}`)
  },
  getSatisfactions() {
    return api.get('/alerts/satisfactions')
  },
  createSatisfaction(data) {
    return api.post('/alerts/satisfactions', data)
  },
  updateSatisfaction(id, data) {
    return api.put(`/alerts/satisfactions/${id}`, data)
  },
  deleteSatisfaction(id) {
    return api.delete(`/alerts/satisfactions/${id}`)
  }
}