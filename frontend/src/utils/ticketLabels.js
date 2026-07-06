import { labelTicketType } from './ticketTypeLabels'

export function ticketTypeLabel(type) {
  return labelTicketType(type) || '—'
}

export function ticketStatusLabel(status) {
  return {
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
    rejected: '已驳回',
    cancelled: '已取消',
  }[status] || status || '—'
}

export function ticketStatusType(status) {
  return {
    pending: 'warning',
    processing: 'primary',
    completed: 'success',
    rejected: 'danger',
    cancelled: 'info',
  }[status] || ''
}
