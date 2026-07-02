import request from '../utils/request'

export function getUsers(params) {
  return request.get('/users', { params })
}

export function createUser(data) {
  return request.post('/users', data)
}

export function batchCreateUsers(data) {
  return request.post('/users/batch', data)
}

export function updateUser(userId, data) {
  return request.put(`/users/${userId}`, data)
}

export function updateUserStatus(userId, action) {
  return request.put(`/users/${userId}/status`, null, { params: { action } })
}

export function resetPassword(userId) {
  return request.post(`/users/${userId}/reset-password`)
}

export function downloadUserTemplate() {
  return request.get('/users/template', { responseType: 'blob' })
}

export function parseUserFile(formData) {
  return request.post('/users/parse-file', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
}
