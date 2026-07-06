/** 工单 type 统一中文标签（与后端 ticket_type_labels 对齐） */
export const TICKET_TYPE_LABELS = {
  证明开具: '证明开具',
  信息变更: '信息变更',
  考勤异常: '考勤异常',
  请假申请: '请假申请',
  离职申请: '离职申请',
  '入职/转正': '入职/转正',
  '报销/薪资': '报销/薪资',
  人工请求: '人工请求',
  其他: '人工请求',
  certify: '证明开具',
  info_change: '信息变更',
  attendance_exception: '考勤异常',
  leave_request: '请假申请',
  reimbursement: '报销/薪资',
  resignation: '离职申请',
  probation: '入职/转正',
  other: '人工请求',
  报销薪资: '报销/薪资',
  入职转正: '入职/转正',
}

export function labelTicketType(raw) {
  if (!raw) return '其他'
  const key = String(raw).trim()
  if (TICKET_TYPE_LABELS[key]) return TICKET_TYPE_LABELS[key]
  if (/[\u4e00-\u9fff]/.test(key)) return key
  return '其他'
}

export function normalizeTicketTypeChartData(items) {
  const merged = {}
  for (const d of items || []) {
    const name = labelTicketType(d.name || d.type)
    merged[name] = (merged[name] || 0) + (d.value || 0)
  }
  return Object.entries(merged).map(([name, value]) => ({ name, value }))
}
