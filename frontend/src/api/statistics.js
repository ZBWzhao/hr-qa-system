import request from '../utils/request'

export function getChartData(chartKey) {
  return request.get(`/statistics/charts/${chartKey}/data`)
}

export function getChartAnalysis(chartKey) {
  return request.get(`/statistics/charts/${chartKey}/analysis`)
}

export function generateChartAnalysis(chartKey) {
  return request.post(`/statistics/charts/${chartKey}/analysis/generate`)
}

export function getDepartments() {
  return request.get('/statistics/departments')
}

export function getTicketByTypeByDept(departmentId) {
  const params = departmentId ? `?department_id=${departmentId}` : ''
  return request.get(`/statistics/charts/ticket_by_type_by_dept/data${params}`)
}

export function getTicketByDeptByType(ticketType) {
  const params = ticketType ? `?ticket_type=${ticketType}` : ''
  return request.get(`/statistics/charts/ticket_by_dept_by_type/data${params}`)
}

export function generateTicketByTypeByDeptAnalysis(departmentId) {
  const params = departmentId ? `?department_id=${departmentId}` : ''
  return request.post(`/statistics/charts/ticket_by_type_by_dept/analysis/generate${params}`)
}

export function generateTicketByDeptByTypeAnalysis(ticketType) {
  const params = ticketType ? `?ticket_type=${ticketType}` : ''
  return request.post(`/statistics/charts/ticket_by_dept_by_type/analysis/generate${params}`)
}

export function generateTopQuestionsGuideAnalysis() {
  return request.post('/statistics/charts/top_questions/guide_analysis')
}
