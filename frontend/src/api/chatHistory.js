import request from '../utils/request'

export function getChatHistory(params) {
  return request.get('/chat/history', { params })
}

export function toggleFavorite(recordId) {
  return request.put(`/chat/history/${recordId}/favorite`)
}

export function deleteHistory(recordId) {
  return request.delete(`/chat/history/${recordId}`)
}
