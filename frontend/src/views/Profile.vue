<template>
  <el-card>
    <template #header><span style="font-weight: 600; color: #111827">个人信息</span></template>
    <el-form :model="form" label-width="80px" style="max-width: 500px">
      <el-form-item label="工号">
        <el-input :value="userStore.userInfo.username" disabled />
      </el-form-item>
      <el-form-item label="姓名">
        <el-input v-model="form.real_name" />
      </el-form-item>
      <el-form-item label="邮箱">
        <el-input v-model="form.email" />
      </el-form-item>
      <el-form-item label="角色">
        <el-tag>{{ roleLabel }}</el-tag>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSave">保存修改</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'
import { updateUserInfo } from '../api/auth'

const userStore = useUserStore()
const form = reactive({ real_name: '', email: '' })
const roleLabel = computed(() => ({ employee: '普通员工', hr: 'HR人员', admin: '管理员' }[userStore.userInfo.role] || ''))

function handleSave() {
  updateUserInfo(form).then(res => {
    userStore.setUser(res.data)
    ElMessage.success('保存成功')
  })
}

onMounted(() => {
  form.real_name = userStore.userInfo.real_name || ''
  form.email = userStore.userInfo.email || ''
})
</script>
