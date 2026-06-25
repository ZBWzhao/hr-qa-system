<template>
  <div class="login-container">
    <div class="bg-decoration">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="dot-grid"></div>
    </div>

    <div class="login-card" :class="{ 'card-visible': cardVisible }">
      <div class="accent-bar"></div>

      <div class="login-header">
        <div class="logo-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM12 20C7.59 20 4 16.41 4 12C4 7.59 7.59 4 12 4C16.41 4 20 7.59 20 12C20 16.41 16.41 20 12 20Z" fill="#D97706"/>
            <circle cx="12" cy="12" r="2" fill="#D97706"/>
          </svg>
        </div>
        <h1>创建账号</h1>
        <p>加入 HR Copilot 智能问答系统</p>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="70px" size="large">
        <el-form-item label="工号" prop="username">
          <el-input v-model="form.username" placeholder="请输入工号" class="custom-input" />
        </el-form-item>
        <el-form-item label="姓名" prop="real_name">
          <el-input v-model="form.real_name" placeholder="请输入姓名" class="custom-input" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱" class="custom-input" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码 (至少6位)" show-password class="custom-input" />
        </el-form-item>
        <el-form-item label="部门" prop="department_id">
          <el-select v-model="form.department_id" placeholder="请选择部门" style="width: 100%">
            <el-option v-for="d in departments" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" class="login-btn" @click="handleRegister">
            <span v-if="!loading">注 册</span>
            <span v-else>注册中...</span>
          </el-button>
        </el-form-item>
      </el-form>

      <div class="footer-links">
        <el-link type="primary" @click="$router.push('/login')">已有账号？返回登录</el-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { register } from '../api/auth'
import { getDepartmentsFlat } from '../api/departments'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref()
const loading = ref(false)
const departments = ref([])
const cardVisible = ref(false)
const form = reactive({ username: '', real_name: '', email: '', password: '', department_id: null })
const rules = {
  username: [{ required: true, message: '请输入工号', trigger: 'blur' }],
  real_name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }, { min: 6, message: '密码至少6位', trigger: 'blur' }]
}

async function fetchDepartments() {
  try {
    const res = await getDepartmentsFlat()
    departments.value = res.data || []
  } catch (e) {}
}

async function handleRegister() {
  await formRef.value.validate()
  loading.value = true
  try {
    const res = await register(form)
    userStore.setToken(res.data.access_token)
    userStore.setUser(res.data.user)
    ElMessage.success('注册成功')
    router.push('/dashboard')
  } catch (e) {} finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchDepartments()
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
  border: 1px solid #D97706;
}

.circle-1 {
  width: 350px;
  height: 350px;
  top: -80px;
  left: -80px;
  animation: float 20s ease-in-out infinite;
  opacity: 0.1;
}

.circle-2 {
  width: 250px;
  height: 250px;
  bottom: -60px;
  right: -60px;
  animation: float 15s ease-in-out infinite reverse;
  opacity: 0.1;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(15px, -15px); }
}

.login-card {
  width: 460px;
  padding: 0 40px 40px;
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

.login-header {
  text-align: center;
  padding: 32px 0 28px;
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

.footer-links {
  text-align: center;
  margin-top: 4px;
}
</style>
