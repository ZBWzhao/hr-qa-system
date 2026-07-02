import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getConversations, getConversationMessages, deleteConversation } from '../api/conversations'

export const useChatStore = defineStore('chat', () => {
  const groups = ref([])
  const currentConversationId = ref(null)
  const messages = ref([])
  const loading = ref(false)

  async function fetchConversations() {
    try {
      const res = await getConversations()
      groups.value = res.data?.groups || []
    } catch (e) {
      groups.value = []
    }
  }

  async function loadConversation(conversationId) {
    loading.value = true
    try {
      const res = await getConversationMessages(conversationId)
      currentConversationId.value = conversationId
      const msgs = res.data?.messages || []
      messages.value = []
      for (const r of msgs) {
        messages.value.push({
          role: 'user',
          content: r.question,
          record_id: r.id,
          feedback: null,
          is_favorite: false,
        })
        messages.value.push({
          role: 'assistant',
          content: r.answer,
          answer_type: r.answer_type,
          source_docs: r.source_docs ? JSON.parse(r.source_docs) : [],
          record_id: r.id,
          feedback: r.feedback,
          is_favorite: !!r.is_favorite,
        })
      }
    } catch (e) {
      messages.value = []
      currentConversationId.value = null
    } finally {
      loading.value = false
    }
  }

  async function removeConversation(conversationId) {
    try {
      await deleteConversation(conversationId)
      if (currentConversationId.value === conversationId) {
        currentConversationId.value = null
        messages.value = []
      }
      await fetchConversations()
    } catch (e) {}
  }

  function clearCurrentConversation() {
    currentConversationId.value = null
    messages.value = []
  }

  // 清除所有聊天数据（用于退出登录时）
  function clearAll() {
    groups.value = []
    currentConversationId.value = null
    messages.value = []
    loading.value = false
  }

  return {
    groups, currentConversationId, messages, loading,
    fetchConversations, loadConversation, removeConversation, clearCurrentConversation, clearAll,
  }
})
