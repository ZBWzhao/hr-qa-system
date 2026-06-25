import request from '../utils/request'

export function getDepartments() {
  return request.get('/departments')
}

export function getDepartmentsFlat() {
  return request.get('/departments/flat')
}

export function createDepartment(data) {
  return request.post('/departments', data)
}

export function updateDepartment(deptId, data) {
  return request.put(`/departments/${deptId}`, data)
}

export function deleteDepartment(deptId) {
  return request.delete(`/departments/${deptId}`)
}
