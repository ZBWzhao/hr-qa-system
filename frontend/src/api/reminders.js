import request from '../utils/request'

export function getReminders() {
  return request.get('/reminders')
}

export function getReminderRules() {
  return request.get('/reminders/rules')
}

export function createReminderRule(data) {
  return request.post('/reminders/rules', data)
}

export function updateReminderRule(ruleId, data) {
  return request.put(`/reminders/rules/${ruleId}`, data)
}
