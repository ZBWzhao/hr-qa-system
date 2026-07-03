<template>
  <div class="login-container">
    <!-- Animated background elements -->
    <div class="bg-decoration">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>
      <div class="line line-1"></div>
      <div class="line line-2"></div>
      <div class="dot-grid"></div>
    </div>

    <div class="login-card" :class="{ 'card-visible': cardVisible }">
      <!-- Top accent bar -->
      <div class="accent-bar"></div>

      <div class="login-header">
        <div class="logo-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM12 20C7.59 20 4 16.41 4 12C4 7.59 7.59 4 12 4C16.41 4 20 7.59 20 12C20 16.41 16.41 20 12 20Z" fill="#D97706"/>
            <path d="M12 6C8.69 6 6 8.69 6 12C6 15.31 8.69 18 12 18C15.31 18 18 15.31 18 12C18 8.69 15.31 6 12 6ZM12 16C9.79 16 8 14.21 8 12C8 9.79 9.79 8 12 8C14.21 8 16 9.79 16 12C16 14.21 14.21 16 12 16Z" fill="#D97706" opacity="0.6"/>
            <circle cx="12" cy="12" r="2" fill="#D97706"/>
          </svg>
        </div>
        <h1>HR Copilot</h1>
        <p>智能制度问答系统</p>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="0" size="large">
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            prefix-icon="User"
            class="custom-input"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
            class="custom-input"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            class="login-btn"
            @click="handleLogin"
          >
            <span v-if="!loading">登 录</span>
            <span v-else>验证中...</span>
          </el-button>
        </el-form-item>
      </el-form>

      <div class="demo-accounts">
        <div class="divider">
          <span>演示账号</span>
        </div>
        <div class="account-tags">
          <span class="account-tag" @click="fillDemo('admin', '123456')">admin</span>
          <span class="account-tag" @click="fillDemo('hr001', '123456')">hr001</span>
          <span class="account-tag" @click="fillDemo('emp001', '123456')">emp001</span>
        </div>
        <p class="demo-hint">密码均为 123456</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login } from '../api/auth'
import { useUserStore } from '../stores/user'
import { useChatStore } from '../stores/chat'

const router = useRouter()
const userStore = useUserStore()
const chatStore = useChatStore()
const formRef = ref()
const loading = ref(false)
const cardVisible = ref(false)
const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

function fillDemo(username, password) {
  form.username = username
  form.password = password
}

async function handleLogin() {
  await formRef.value.validate()
  loading.value = true
  try {
    const res = await login(form)

    // 清除旧的聊天数据（防止切换账号时数据串号）
    chatStore.clearAll()
    // 清除笔记缓存
    Object.keys(localStorage).forEach(key => {
      if (key.startsWith('chat-notes-')) {
        localStorage.removeItem(key)
      }
    })

    // 设置新用户信息
    userStore.setToken(res.data.access_token)
    userStore.setUser(res.data.user)
    ElMessage.success('登录成功')
    router.push(res.data.user.role === 'admin' ? '/user-management' : '/chat')
  } catch (e) {} finally {
    loading.value = false
  }
}

onMounted(() => {
  setTimeout(() => {
    cardVisible.value = true
  }, 100)
})
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fafafa;
  position: relative;
  overflow: hidden;
}

/* Background decorations */
.bg-decoration {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.dot-grid {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(circle, #e5e7eb 1px, transparent 1px);
  background-size: 32px 32px;
  opacity: 0.5;
}

.circle {
  position: absolute;
  border-radius: 50%;
  border: 1px solid #e5e7eb;
}

.circle-1 {
  width: 400px;
  height: 400px;
  top: -100px;
  right: -100px;
  animation: float 20s ease-in-out infinite;
  border-color: #D97706;
  opacity: 0.15;
}

.circle-2 {
  width: 300px;
  height: 300px;
  bottom: -80px;
  left: -80px;
  animation: float 15s ease-in-out infinite reverse;
  border-color: #D97706;
  opacity: 0.1;
}

.circle-3 {
  width: 200px;
  height: 200px;
  top: 50%;
  left: 10%;
  animation: float 18s ease-in-out infinite 2s;
  border-color: #e5e7eb;
  opacity: 0.3;
}

.line {
  position: absolute;
  height: 1px;
  background: linear-gradient(90deg, transparent, #D97706, transparent);
  opacity: 0.1;
}

.line-1 {
  width: 300px;
  top: 30%;
  right: 10%;
  transform: rotate(-15deg);
  animation: shimmer 8s ease-in-out infinite;
}

.line-2 {
  width: 200px;
  bottom: 25%;
  left: 15%;
  transform: rotate(10deg);
  animation: shimmer 6s ease-in-out infinite 1s;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  25% { transform: translate(10px, -15px) rotate(2deg); }
  50% { transform: translate(-5px, 10px) rotate(-1deg); }
  75% { transform: translate(8px, 5px) rotate(1deg); }
}

@keyframes shimmer {
  0%, 100% { opacity: 0.05; transform: rotate(-15deg) scaleX(1); }
  50% { opacity: 0.15; transform: rotate(-15deg) scaleX(1.2); }
}

/* Card */
.login-card {
  width: min(92vw, 400px);
  padding: 0 24px 32px;
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 8px 32px rgba(0, 0, 0, 0.06);
  border: 1px solid #f0f0f0;
  position: relative;
  z-index: 10;
  opacity: 0;
  transform: translateY(30px) scale(0.98);
  transition: all 0.7s cubic-bezier(0.16, 1, 0.3, 1);
}

.login-card.card-visible {
  opacity: 1;
  transform: translateY(0) scale(1);
}

.accent-bar {
  height: 3px;
  background: linear-gradient(90deg, #D97706, #F59E0B, #D97706);
  border-radius: 20px 20px 0 0;
  background-size: 200% 100%;
  animation: gradientMove 3s ease-in-out infinite;
}

@keyframes gradientMove {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

/* Header */
.login-header {
  text-align: center;
  padding: 36px 0 32px;
}

.logo-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  background: #FFF7ED;
  border-radius: 16px;
  margin-bottom: 16px;
  animation: pulse 3s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(217, 119, 6, 0.1); }
  50% { box-shadow: 0 0 0 12px rgba(217, 119, 6, 0); }
}

.login-header h1 {
  margin: 0 0 6px;
  color: #111827;
  font-size: 26px;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.login-header p {
  color: #9CA3AF;
  font-size: 14px;
  margin: 0;
}

/* Form */
.custom-input :deep(.el-input__wrapper) {
  border-radius: 10px;
  box-shadow: 0 0 0 1px #e5e7eb inset;
  transition: all 0.3s;
}

.custom-input :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #D97706 inset;
}

.custom-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px rgba(217, 119, 6, 0.2) inset;
}

.login-btn {
  width: 100%;
  height: 48px;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 500;
  letter-spacing: 2px;
  transition: all 0.3s;
}

.login-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(217, 119, 6, 0.3);
}

.login-btn:active {
  transform: translateY(0);
}

/* Footer */
.footer-links {
  text-align: center;
  margin-top: 4px;
}

.demo-accounts {
  margin-top: 28px;
}

.divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: #f3f4f6;
}

.divider span {
  color: #9CA3AF;
  font-size: 12px;
  white-space: nowrap;
}

.account-tags {
  display: flex;
  justify-content: center;
  gap: 8px;
}

.account-tag {
  padding: 6px 16px;
  background: #f9fafb;
  border: 1px solid #f3f4f6;
  border-radius: 8px;
  font-size: 13px;
  color: #6B7280;
  cursor: pointer;
  transition: all 0.2s;
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
}

.account-tag:hover {
  background: #FFF7ED;
  border-color: #D97706;
  color: #D97706;
  transform: translateY(-1px);
}

.demo-hint {
  text-align: center;
  color: #D1D5DB;
  font-size: 11px;
  margin: 10px 0 0;
}
</style>
