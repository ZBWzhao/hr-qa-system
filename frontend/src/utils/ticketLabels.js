export const TICKET_TYPE_LABELS = {
  certify: '证明开具',
  info_change: '信息变更',
  attendance_exception: '考勤异常',
  leave_request: '请假申请',
  resignation: '离职申请',
  onboarding_probation: '入职/转正',
  reimbursement: '报销/薪资',
  other: '其他',
}

export function ticketTypeLabel(type) {
  return TICKET_TYPE_LABELS[type] || type || '—'
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
