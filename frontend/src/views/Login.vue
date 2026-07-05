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

    <div class="login-layout" :class="{ 'card-visible': cardVisible }">
      <!-- 左侧：登录表单 -->
      <div class="login-card">
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
              @keyup.enter="handleLogin"
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

        <div class="register-link">
          <span>还没有账号？</span>
          <router-link to="/register">立即注册</router-link>
        </div>
      </div>

      <!-- 右侧：用户列表 -->
      <div class="users-panel">
        <div class="panel-header">
          <span class="panel-title">快速登录</span>
          <span class="panel-hint">点击行自动填入 · 密码均为 123456</span>
        </div>
        <div class="user-table-wrap">
          <table class="user-table" v-if="demoUsers.length">
            <thead>
              <tr>
                <th>用户名</th>
                <th>姓名</th>
                <th>角色</th>
                <th>部门</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="u in demoUsers"
                :key="u.username"
                class="user-row"
                :class="{ 'row-admin': u.role === 'admin', 'row-hr': u.role === 'hr' }"
                @click="fillDemo(u.username, '123456')"
              >
                <td class="col-username">{{ u.username }}</td>
                <td>{{ u.real_name }}</td>
                <td>
                  <span class="role-tag" :class="'role-' + u.role">{{ roleLabel(u.role) }}</span>
                </td>
                <td>{{ u.department_name }}</td>
              </tr>
            </tbody>
          </table>
          <p v-else class="demo-hint">加载中...</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login, getDemoAccounts } from '../api/auth'
import { useUserStore } from '../stores/user'
import { useChatStore } from '../stores/chat'

const router = useRouter()
const userStore = useUserStore()
const chatStore = useChatStore()
const formRef = ref()
const loading = ref(false)
const cardVisible = ref(false)
const demoUsers = ref([])
const form = reactive({ username: '', password: '' })

const roleLabel = (role) => ({ admin: '管理员', hr: 'HR', employee: '员工' }[role] || role)
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
  // 加载演示账号列表
  getDemoAccounts().then(res => {
    demoUsers.value = res.data || []
  }).catch(() => {})
})
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: #fafafa;
  position: relative;
  overflow: hidden;
  box-sizing: border-box;
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

/* Layout */
.login-layout {
  display: flex;
  gap: 20px;
  align-items: stretch;
  position: relative;
  z-index: 10;
  opacity: 0;
  transform: translateY(30px) scale(0.98);
  transition: all 0.7s cubic-bezier(0.16, 1, 0.3, 1);
}

.login-layout.card-visible {
  opacity: 1;
  transform: translateY(0) scale(1);
}

/* Card */
.login-card {
  width: 400px;
  min-width: 360px;
  padding: 0 24px 28px;
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 8px 32px rgba(0, 0, 0, 0.06);
  border: 1px solid #f0f0f0;
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
  padding: 28px 0 24px;
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

/* Register link */
.register-link {
  text-align: center;
  margin-top: 16px;
  font-size: 13px;
  color: #9CA3AF;
}

.register-link a {
  color: #D97706;
  text-decoration: none;
  font-weight: 500;
}

.register-link a:hover {
  text-decoration: underline;
}

/* Right panel */
.users-panel {
  flex: 1;
  min-width: 420px;
  max-width: 560px;
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 8px 32px rgba(0, 0, 0, 0.06);
  border: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  padding: 16px 20px 12px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.panel-title {
  font-size: 15px;
  font-weight: 600;
  color: #111827;
}

.panel-hint {
  font-size: 12px;
  color: #9CA3AF;
}

.user-table-wrap {
  flex: 1;
  overflow-y: auto;
  max-height: 480px;
}

.user-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.user-table thead {
  position: sticky;
  top: 0;
  z-index: 1;
}

.user-table th {
  background: #f9fafb;
  color: #6b7280;
  font-weight: 500;
  padding: 8px 10px;
  text-align: left;
  border-bottom: 1px solid #f0f0f0;
  font-size: 12px;
}

.user-table td {
  padding: 7px 10px;
  border-bottom: 1px solid #f8f8f8;
  color: #374151;
}

.col-username {
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  color: #6B7280;
}

.user-row {
  cursor: pointer;
  transition: background 0.15s;
}

.user-row:hover {
  background: #FFF7ED;
}

.user-row:last-child td {
  border-bottom: none;
}

.row-admin {
  background: #fefce8;
}

.row-admin:hover {
  background: #fef9c3;
}

.row-hr {
  background: #f0f9ff;
}

.row-hr:hover {
  background: #e0f2fe;
}

.role-tag {
  display: inline-block;
  padding: 1px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.role-admin {
  background: #fef3c7;
  color: #92400e;
}

.role-hr {
  background: #dbeafe;
  color: #1e40af;
}

.role-employee {
  background: #f3f4f6;
  color: #6b7280;
}

.demo-hint {
  text-align: center;
  color: #D1D5DB;
  font-size: 11px;
  margin: 10px 0 0;
}

/* Responsive: stack on narrow screens */
@media (max-width: 860px) {
  .login-layout {
    flex-direction: column;
    align-items: center;
  }
  .login-card {
    width: min(92vw, 400px);
    min-width: auto;
  }
  .users-panel {
    width: min(92vw, 500px);
    min-width: auto;
    max-width: none;
  }
}
</style>
