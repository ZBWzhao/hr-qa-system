import request from '../utils/request'

export function getConversations() {
  return request.get('/chat/conversations')
}

export function getConversationMessages(conversationId) {
  return request.get(`/chat/conversations/${conversationId}/messages`)
}

export function deleteConversation(conversationId) {
  return request.delete(`/chat/conversations/${conversationId}`)
}
