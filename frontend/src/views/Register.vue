<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1>用户注册</h1>
        <p>HR Copilot 智能问答系统</p>
      </div>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px" size="large">
        <el-form-item label="工号" prop="username">
          <el-input v-model="form.username" placeholder="请输入工号" />
        </el-form-item>
        <el-form-item label="姓名" prop="real_name">
          <el-input v-model="form.real_name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-form-item label="部门" prop="department_id">
          <el-select v-model="form.department_id" placeholder="请选择部门" style="width: 100%">
            <el-option v-for="d in departments" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" style="width: 100%" @click="handleRegister">注 册</el-button>
        </el-form-item>
      </el-form>
      <div style="text-align: center">
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

onMounted(() => fetchDepartments())
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-card {
  width: 460px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}
.login-header {
  text-align: center;
  margin-bottom: 30px;
}
.login-header h1 {
  margin: 0 0 5px;
  color: #333;
  font-size: 24px;
}
.login-header p {
  color: #999;
  font-size: 14px;
}
</style>
