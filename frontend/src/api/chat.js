import request from '../utils/request'

export function sendChat(data) {
  return request.post('/chat', data)
}

export function saveChatRecord(data) {
  return request.post('/chat/save-record', data)
}

export function voiceChat() {
  return request.post('/chat/voice')
}

export function imageChat() {
  return request.post('/chat/image')
}

export function getChatStats() {
  return request.get('/chat/stats')
}

export function reindexDocuments() {
  return request.post('/documents/reindex')
}
