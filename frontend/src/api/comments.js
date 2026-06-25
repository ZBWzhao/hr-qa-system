import request from '../utils/request'

export function getComments(params) {
  return request.get('/comments', { params })
}

export function createComment(data) {
  return request.post('/comments', data)
}

export function likeComment(commentId) {
  return request.put(`/comments/${commentId}/like`)
}

export function adoptComment(commentId) {
  return request.put(`/comments/${commentId}/adopt`)
}

export function deleteComment(commentId) {
  return request.delete(`/comments/${commentId}`)
}
