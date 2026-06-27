import api from './auth'

export const feedbackApi = {
  getFeedbacks(params) {
    return api.get('/feedback/feedbacks', { params })
  },
  createFeedback(data) {
    return api.post('/feedback/feedbacks', data)
  },
  updateFeedback(id, data) {
    return api.put(`/feedback/feedbacks/${id}`, data)
  },
  deleteFeedback(id) {
    return api.delete(`/feedback/feedbacks/${id}`)
  },
  getSatisfactions() {
    return api.get('/feedback/satisfactions')
  },
  createSatisfaction(data) {
    return api.post('/feedback/satisfactions', data)
  },
  updateSatisfaction(id, data) {
    return api.put(`/feedback/satisfactions/${id}`, data)
  },
  deleteSatisfaction(id) {
    return api.delete(`/feedback/satisfactions/${id}`)
  }
}
