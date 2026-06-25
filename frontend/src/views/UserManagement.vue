<template>
  <el-card>
    <template #header><span style="font-weight: 600; color: #111827">用户管理</span></template>
    <el-table :data="users" v-loading="loading" stripe>
      <el-table-column prop="username" label="工号" width="120" />
      <el-table-column prop="real_name" label="姓名" width="120" />
      <el-table-column prop="email" label="邮箱" min-width="180" />
      <el-table-column prop="role" label="角色" width="120">
        <template #default="{ row }"><el-tag :type="roleType(row.role)" size="small">{{ roleLabel(row.role) }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }"><el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small">{{ row.status === 1 ? '正常' : '禁用' }}</el-tag></template>
      </el-table-column>
      <el-table-column label="操作" width="280">
        <template #default="{ row }">
          <el-button size="small" @click="showEdit(row)">编辑</el-button>
          <el-button size="small" :type="row.status === 1 ? 'warning' : 'success'" @click="toggleStatus(row)">{{ row.status === 1 ? '禁用' : '启用' }}</el-button>
          <el-button size="small" type="danger" @click="handleReset(row)">重置密码</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination style="margin-top: 16px; justify-content: center" :current-page="page" :page-size="20" :total="total" layout="prev, pager, next" @current-change="p => { page = p; fetchData() }" />

    <el-dialog v-model="editVisible" title="编辑用户" width="500px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="姓名"><el-input v-model="editForm.real_name" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="editForm.email" /></el-form-item>
        <el-form-item label="角色">
          <el-select v-model="editForm.role">
            <el-option label="普通员工" value="employee" />
            <el-option label="HR人员" value="hr" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEdit">确定</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getUsers, updateUser, resetPassword } from '../api/users'

const loading = ref(false)
const users = ref([])
const page = ref(1)
const total = ref(0)
const editVisible = ref(false)
const editId = ref(null)
const editForm = reactive({ real_name: '', email: '', role: 'employee' })

function roleType(r) { return { employee: '', hr: 'success', admin: 'danger' }[r] || '' }
function roleLabel(r) { return { employee: '普通员工', hr: 'HR人员', admin: '管理员' }[r] || r }

async function fetchData() {
  loading.value = true
  try {
    const res = await getUsers({ page: page.value })
    users.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch (e) {} finally { loading.value = false }
}

function showEdit(row) {
  editId.value = row.id
  Object.assign(editForm, { real_name: row.real_name, email: row.email, role: row.role })
  editVisible.value = true
}

async function submitEdit() {
  await updateUser(editId.value, editForm)
  ElMessage.success('修改成功')
  editVisible.value = false
  fetchData()
}

async function toggleStatus(row) {
  await updateUser(row.id, { status: row.status === 1 ? 0 : 1 })
  ElMessage.success('操作成功')
  fetchData()
}

async function handleReset(row) {
  await ElMessageBox.confirm(`确认重置 ${row.real_name} 的密码为 123456？`, '提示', { type: 'warning' })
  await resetPassword(row.id)
  ElMessage.success('密码已重置为 123456')
}

onMounted(() => fetchData())
</script>
