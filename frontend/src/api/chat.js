import request from '../utils/request'

export function sendChat(data) {
  return request.post('/chat', data)
}

export function voiceChat() {
  return request.post('/chat/voice')
}

export function imageChat() {
  return request.post('/chat/image')
}
