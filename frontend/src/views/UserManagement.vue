<template>
  <el-card>
    <template #header>
      <div style="display: flex; justify-content: space-between; align-items: center">
        <span style="font-weight: 600; color: #111827">用户管理</span>
        <div style="display: flex; gap: 8px">
          <el-button type="primary" @click="showAddSingle">
            <el-icon style="margin-right: 4px"><Plus /></el-icon>
            添加用户
          </el-button>
          <el-button type="success" @click="showAddBatch">
            <el-icon style="margin-right: 4px"><Upload /></el-icon>
            批量添加
          </el-button>
        </div>
      </div>
    </template>
    <div style="display: flex; gap: 12px; margin-bottom: 16px">
      <el-select v-model="statusFilter" placeholder="全部状态" clearable @change="fetchData" style="width: 160px">
        <el-option label="全部" value="" />
        <el-option label="待审核" :value="0" />
        <el-option label="已启用" :value="1" />
        <el-option label="已禁用" :value="2" />
        <el-option label="已拒绝" :value="3" />
      </el-select>
    </div>
    <el-table :data="users" v-loading="loading" stripe>
      <el-table-column prop="username" label="工号/登录账号" width="120" />
      <el-table-column prop="real_name" label="姓名" width="120" />
      <el-table-column prop="email" label="邮箱" min-width="180" />
      <el-table-column prop="role" label="角色" width="120">
        <template #default="{ row }"><el-tag :type="roleType(row.role)" size="small">{{ roleLabel(row.role) }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }"><el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag></template>
      </el-table-column>
      <el-table-column label="操作" width="320">
        <template #default="{ row }">
          <el-button size="small" @click="showEdit(row)">编辑</el-button>
          <template v-if="row.status === 0">
            <el-button size="small" type="success" @click="handleAction(row, 'approve')">通过</el-button>
            <el-button size="small" type="danger" @click="handleAction(row, 'reject')">拒绝</el-button>
          </template>
          <template v-else-if="row.status === 1">
            <el-button size="small" type="warning" @click="handleAction(row, 'disable')">禁用</el-button>
          </template>
          <template v-else-if="row.status === 2">
            <el-button size="small" type="success" @click="handleAction(row, 'enable')">启用</el-button>
          </template>
          <template v-else-if="row.status === 3">
            <el-button size="small" type="success" @click="handleAction(row, 'approve')">通过</el-button>
          </template>
          <el-button size="small" type="danger" @click="handleReset(row)">重置密码</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination style="margin-top: 16px; justify-content: center" :current-page="page" :page-size="20" :total="total" layout="prev, pager, next" @current-change="p => { page = p; fetchData() }" />

    <!-- 编辑用户对话框 -->
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

    <!-- 单个添加用户对话框 -->
    <el-dialog v-model="addSingleVisible" title="添加用户" width="500px">
      <el-form :model="addSingleForm" :rules="addSingleRules" ref="addSingleFormRef" label-width="100px">
        <el-form-item label="工号/账号" prop="username">
          <el-input v-model="addSingleForm.username" placeholder="用于登录的工号" />
        </el-form-item>
        <el-form-item label="姓名" prop="real_name">
          <el-input v-model="addSingleForm.real_name" placeholder="真实姓名" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="addSingleForm.email" placeholder="工作邮箱" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="addSingleForm.role">
            <el-option label="普通员工" value="employee" />
            <el-option label="HR人员" value="hr" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="初始密码">
          <el-input v-model="addSingleForm.password" placeholder="默认为 123456" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addSingleVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAddSingle" :loading="addSingleLoading">确定</el-button>
      </template>
    </el-dialog>

    <!-- 批量添加用户对话框 -->
    <el-dialog v-model="addBatchVisible" title="批量添加用户" width="600px">
      <div style="margin-bottom: 16px">
        <p style="color: #6B7280; font-size: 14px; margin-bottom: 12px">
          请按照以下格式填写用户信息，每行一个用户，字段用逗号分隔：
        </p>
        <div style="background: #f9fafb; padding: 12px; border-radius: 8px; font-size: 13px; color: #374151; font-family: monospace">
          格式：工号,姓名,邮箱,角色
          <br>
          示例：
          <br>
          emp002,张三,zhangsan@company.com,employee
          <br>
          hr002,李四,lisi@company.com,hr
        </div>
        <p style="color: #9CA3AF; font-size: 12px; margin-top: 8px">
          角色可选：employee（普通员工）、hr（HR人员）、admin（管理员）
          <br>
          初始密码默认为 123456
        </p>
      </div>
      <el-input
        v-model="batchText"
        type="textarea"
        :rows="10"
        placeholder="请粘贴或输入用户数据，每行一个用户..."
      />
      <div v-if="batchResult" style="margin-top: 12px">
        <el-divider />
        <h4 style="margin-bottom: 8px">导入结果</h4>
        <p style="color: #059669">成功：{{ batchResult.success }} 条</p>
        <p v-if="batchResult.failed > 0" style="color: #DC2626">失败：{{ batchResult.failed }} 条</p>
        <div v-if="batchResult.errors?.length" style="margin-top: 8px; max-height: 150px; overflow-y: auto">
          <p v-for="(err, i) in batchResult.errors" :key="i" style="color: #DC2626; font-size: 13px">{{ err }}</p>
        </div>
      </div>
      <template #footer>
        <el-button @click="addBatchVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAddBatch" :loading="addBatchLoading">导入</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Upload } from '@element-plus/icons-vue'
import { getUsers, updateUser, updateUserStatus, resetPassword, createUser, batchCreateUsers } from '../api/users'

const loading = ref(false)
const users = ref([])
const page = ref(1)
const total = ref(0)
const statusFilter = ref('')
const editVisible = ref(false)
const editId = ref(null)
const editForm = reactive({ real_name: '', email: '', role: 'employee' })

// 单个添加
const addSingleVisible = ref(false)
const addSingleLoading = ref(false)
const addSingleFormRef = ref(null)
const addSingleForm = reactive({
  username: '',
  real_name: '',
  email: '',
  role: 'employee',
  password: '123456'
})
const addSingleRules = {
  username: [{ required: true, message: '请输入工号', trigger: 'blur' }],
  real_name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}

// 批量添加
const addBatchVisible = ref(false)
const addBatchLoading = ref(false)
const batchText = ref('')
const batchResult = ref(null)

function roleType(r) { return { employee: '', hr: 'success', admin: 'danger' }[r] || '' }
function roleLabel(r) { return { employee: '普通员工', hr: 'HR人员', admin: '管理员' }[r] || r }
function statusType(s) { return { 0: 'warning', 1: 'success', 2: 'danger', 3: 'info' }[s] || '' }
function statusLabel(s) { return { 0: '待审核', 1: '已启用', 2: '已禁用', 3: '已拒绝' }[s] || '未知' }

async function fetchData() {
  loading.value = true
  try {
    const params = { page: page.value }
    if (statusFilter.value !== '' && statusFilter.value !== null) params.status = statusFilter.value
    const res = await getUsers(params)
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

async function handleAction(row, action) {
  const actionLabel = { approve: '通过', reject: '拒绝', enable: '启用', disable: '禁用' }[action]
  await ElMessageBox.confirm(`确认${actionLabel}用户 ${row.real_name}？`, '提示', { type: 'warning' })
  await updateUserStatus(row.id, action)
  ElMessage.success('操作成功')
  fetchData()
}

async function handleReset(row) {
  await ElMessageBox.confirm(`确认重置 ${row.real_name} 的密码为 123456？`, '提示', { type: 'warning' })
  await resetPassword(row.id)
  ElMessage.success('密码已重置为 123456')
}

// 单个添加用户
function showAddSingle() {
  Object.assign(addSingleForm, {
    username: '',
    real_name: '',
    email: '',
    role: 'employee',
    password: '123456'
  })
  addSingleVisible.value = true
}

async function submitAddSingle() {
  try {
    await addSingleFormRef.value.validate()
  } catch (e) {
    return
  }

  addSingleLoading.value = true
  try {
    await createUser(addSingleForm)
    ElMessage.success('用户添加成功')
    addSingleVisible.value = false
    fetchData()
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '添加失败')
  } finally {
    addSingleLoading.value = false
  }
}

// 批量添加用户
function showAddBatch() {
  batchText.value = ''
  batchResult.value = null
  addBatchVisible.value = true
}

async function submitAddBatch() {
  if (!batchText.value.trim()) {
    ElMessage.warning('请输入用户数据')
    return
  }

  // 解析文本
  const lines = batchText.value.trim().split('\n').filter(line => line.trim())
  const users = []

  for (let i = 0; i < lines.length; i++) {
    const parts = lines[i].split(',').map(s => s.trim())
    if (parts.length < 3) {
      ElMessage.error(`第 ${i + 1} 行格式错误，至少需要工号、姓名、邮箱`)
      return
    }

    const [username, real_name, email, role = 'employee'] = parts
    const validRoles = ['employee', 'hr', 'admin']
    if (!validRoles.includes(role)) {
      ElMessage.error(`第 ${i + 1} 行角色错误，可选：employee、hr、admin`)
      return
    }

    users.push({
      username,
      real_name,
      email,
      role,
      password: '123456'
    })
  }

  addBatchLoading.value = true
  try {
    const res = await batchCreateUsers({ users })
    batchResult.value = res.data
    ElMessage.success(`导入完成：成功 ${res.data.success} 条`)
    fetchData()
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '导入失败')
  } finally {
    addBatchLoading.value = false
  }
}

onMounted(() => fetchData())
</script>
