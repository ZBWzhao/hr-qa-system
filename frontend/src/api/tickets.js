import request from '../utils/request'

export function getTickets(params) {
  return request.get('/tickets', { params })
}

export function getTicket(ticketId) {
  return request.get(`/tickets/detail/${ticketId}`)
}

export function createTicket(data) {
  return request.post('/tickets', data)
}

export function updateTicket(ticketId, data) {
  return request.put(`/tickets/${ticketId}`, data)
}

export function getTicketStats() {
  return request.get('/tickets/stats')
}
