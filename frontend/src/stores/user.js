import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getUserInfo } from '../api/auth'
import { useChatStore } from './chat'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('user') || '{}'))

  const isLoggedIn = computed(() => !!token.value)
  const role = computed(() => userInfo.value.role || '')
  const isHR = computed(() => role.value === 'hr')
  const isAdmin = computed(() => role.value === 'admin')
  const departmentId = computed(() => userInfo.value.department_id || null)
  const departmentName = computed(() => userInfo.value.department_name || '')

  function setToken(t) {
    token.value = t
    localStorage.setItem('token', t)
  }

  function setUser(u) {
    userInfo.value = u
    localStorage.setItem('user', JSON.stringify(u))
  }

  async function fetchUserInfo() {
    try {
      const res = await getUserInfo()
      setUser(res.data)
      return res.data
    } catch (e) {
      return null
    }
  }

  function logout() {
    // 清除聊天记录
    const chatStore = useChatStore()
    chatStore.clearAll()

    // 清除用户信息
    token.value = ''
    userInfo.value = {}
    localStorage.removeItem('token')
    localStorage.removeItem('user')

    // 清除笔记缓存
    Object.keys(localStorage).forEach(key => {
      if (key.startsWith('chat-notes-')) {
        localStorage.removeItem(key)
      }
    })
  }

  return { token, userInfo, isLoggedIn, role, isHR, isAdmin, departmentId, departmentName, setToken, setUser, fetchUserInfo, logout }
})