/** 问答 answer_type 统一中文标签 */
export const ANSWER_TYPE_LABELS = {
  faq: '标准答案',
  rule: '规则匹配',
  rag: '文档检索',
  miss: '未命中',
  clarification: '澄清追问',
  followup_clarification: '追问澄清',
  followup_no_context: '追问澄清',
  ticket_form: '工单申请',
  ticket_clarification: '工单申请',
  ticket_qa: '工单咨询',
  ticket_confirm: '工单确认',
  ticket_submitted: '工单已提交',
  notice_form: '公告发布',
  notice_clarification: '公告发布',
  notice_confirm: '公告确认',
  notice_published: '公告已发布',
  no_permission: '无权限',
  system: '系统消息',
  mock: '模拟问答',
  error: '系统异常',
}

/** 将 answer_type 或已有标签转为中文；未知英文 key 不直接展示 */
export function labelAnswerType(raw) {
  if (!raw) return '其他'
  const key = String(raw).trim()
  if (ANSWER_TYPE_LABELS[key]) return ANSWER_TYPE_LABELS[key]
  if (/[\u4e00-\u9fff]/.test(key)) return key
  if (key.startsWith('notice_')) return '公告相关'
  if (key.startsWith('ticket_')) return '工单相关'
  return '其他'
}

/** 合并同名类别并转为中文标签，供饼图使用 */
export function normalizeCategoryChartData(items) {
  const merged = {}
  for (const d of items || []) {
    const name = labelAnswerType(d.name || d.type)
    merged[name] = (merged[name] || 0) + (d.value || 0)
  }
  return Object.entries(merged).map(([name, value]) => ({ name, value }))
}
