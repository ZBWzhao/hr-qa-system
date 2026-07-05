import request from '../utils/request'

export function getDemoAccounts() {
  return request.get('/auth/demo-accounts')
}

export function login(data) {
  return request.post('/auth/login', data)
}

export function register(data) {
  return request.post('/auth/register', data)
}

export function getUserInfo() {
  return request.get('/auth/users/me')
}

export function updateUserInfo(data) {
  return request.put('/auth/users/me', data)
}
