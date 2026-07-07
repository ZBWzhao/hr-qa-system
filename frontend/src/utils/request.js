import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 60000
})

request.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

request.interceptors.response.use(
  response => {
    if (response.config.responseType === 'blob') {
      const blob = response.data
      if (blob?.type === 'application/json') {
        return blob.text().then(text => {
          try {
            const res = JSON.parse(text)
            ElMessage.error(res.message || '下载失败')
          } catch {
            ElMessage.error('下载失败')
          }
          return Promise.reject(new Error('download failed'))
        })
      }
      return blob
    }
    const res = response.data
    if (res.code !== 0) {
      if (res.code === 401) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        router.push('/login')
      } else if (res.code === 403) {
        // 403 静默处理，不弹 toast（后台请求不应打扰用户）
      } else {
        ElMessage.error(res.message || '请求失败')
      }
      return Promise.reject(new Error(res.message))
    }
    return res
  },
  error => {
    if (error.response) {
      if (error.response.status === 401) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        router.push('/login')
      } else if (error.response.status === 403) {
        // 403 静默处理，不弹 toast
      } else {
        ElMessage.error(error.response.data?.message || '网络错误')
      }
    } else {
      ElMessage.error('网络连接失败')
    }
    return Promise.reject(error)
  }
)

export default request
