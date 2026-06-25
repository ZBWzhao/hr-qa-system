import request from '../utils/request'

export function getNotices(params) {
  return request.get('/notices', { params })
}

export function getNotice(noticeId) {
  return request.get(`/notices/${noticeId}`)
}

export function createNotice(data) {
  return request.post('/notices', data)
}

export function updateNotice(noticeId, data) {
  return request.put(`/notices/${noticeId}`, data)
}

export function deleteNotice(noticeId) {
  return request.delete(`/notices/${noticeId}`)
}

export function getUnreadCount() {
  return request.get('/notices/unread-count')
}
