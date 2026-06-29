import request from '../utils/request'

export function getUsers(params) {
  return request.get('/users', { params })
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
