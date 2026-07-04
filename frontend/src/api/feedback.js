import request from '../utils/request'

export function createFeedback(data) {
  return request.post('/feedback', data)
}

export function getFeedbacks(params) {
  return request.get('/feedback', { params })
}

export function handleFeedback(feedbackId, data) {
  return request.put(`/feedback/${feedbackId}/handle`, data)
}

export function getFeedbackStats() {
  return request.get('/feedback/stats')
}

export function getFeedbackSuggestion(feedbackId) {
  return request.get(`/feedback/${feedbackId}/suggestion`)
}

export function generateFeedbackSuggestion(feedbackId, force = false) {
  return request.post(`/feedback/${feedbackId}/suggestion`, null, {
    params: force ? { force: 1 } : {},
  })
}
