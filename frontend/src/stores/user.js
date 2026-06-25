import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getUserInfo } from '../api/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('user') || '{}'))

  const isLoggedIn = computed(() => !!token.value)
  const role = computed(() => userInfo.value.role || '')
  const isHR = computed(() => ['hr', 'admin'].includes(role.value))
  const isAdmin = computed(() => role.value === 'admin')

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
    token.value = ''
    userInfo.value = {}
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return { token, userInfo, isLoggedIn, role, isHR, isAdmin, setToken, setUser, fetchUserInfo, logout }
})