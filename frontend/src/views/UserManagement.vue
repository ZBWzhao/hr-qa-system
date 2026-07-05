<template>
  <el-card>
    <template #header>
      <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px">
        <span style="font-weight: 600; color: #111827">用户管理</span>
        <div style="display: flex; gap: 8px; flex-wrap: wrap">
          <el-button type="primary" @click="showAddSingle">
            <el-icon style="margin-right: 4px"><Plus /></el-icon>
            添加用户
          </el-button>
          <el-button type="success" @click="showAddBatch">
            <el-icon style="margin-right: 4px"><Upload /></el-icon>
            批量导入
          </el-button>
        </div>
      </div>
    </template>
    <div style="display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap">
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
      <el-table-column prop="department_id" label="部门" width="120">
        <template #default="{ row }">{{ getDeptName(row.department_id) }}</template>
      </el-table-column>
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
        <el-form-item label="部门">
          <el-select v-model="editForm.department_id" placeholder="请选择部门" clearable>
            <el-option v-for="dept in departments" :key="dept.id" :label="dept.name" :value="dept.id" />
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

    <!-- 批量导入对话框 - 步骤1：上传文件 -->
    <el-dialog v-model="addBatchVisible" title="批量导入用户" width="700px" :close-on-click-modal="false">
      <el-steps :active="batchStep" finish-status="success" style="margin-bottom: 24px">
        <el-step title="上传文件" />
        <el-step title="预览确认" />
        <el-step title="导入结果" />
      </el-steps>

      <!-- 步骤1：上传文件 -->
      <div v-if="batchStep === 0">
        <div style="margin-bottom: 16px">
          <el-button type="primary" plain @click="downloadTemplate">
            <el-icon style="margin-right: 4px"><Download /></el-icon>
            下载模板文件
          </el-button>
          <span style="margin-left: 12px; color: #9CA3AF; font-size: 13px">请使用模板文件填写用户信息后上传</span>
        </div>

        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :limit="1"
          :on-change="handleFileChange"
          :on-remove="handleFileRemove"
          accept=".csv,.xlsx,.xls"
          drag
        >
          <el-icon style="font-size: 48px; color: #C0C4CC; margin-bottom: 12px"><Upload /></el-icon>
          <div style="color: #606266">将文件拖到此处，或<em style="color: #409EFF">点击上传</em></div>
          <template #tip>
            <div style="color: #9CA3AF; font-size: 12px; margin-top: 8px">支持 .csv、.xlsx、.xls 格式文件</div>
          </template>
        </el-upload>
      </div>

      <!-- 步骤2：预览确认 -->
      <div v-if="batchStep === 1">
        <div style="margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center">
          <div>
            <span style="color: #374151; font-weight: 500">预览用户列表</span>
            <span style="margin-left: 8px; color: #9CA3AF; font-size: 13px">已选择 {{ selectedUsers.length }} / {{ previewUsers.length }} 个用户</span>
          </div>
          <div>
            <el-button size="small" @click="selectAllUsers">全部选择</el-button>
            <el-button size="small" @click="deselectAllUsers">全部取消</el-button>
          </div>
        </div>

        <el-table :data="previewUsers" stripe max-height="400" @selection-change="handleSelectionChange">
          <el-table-column type="selection" width="50" />
          <el-table-column prop="username" label="工号" width="100" />
          <el-table-column prop="real_name" label="姓名" width="100" />
          <el-table-column prop="email" label="邮箱" min-width="180" />
          <el-table-column prop="role" label="角色" width="100">
            <template #default="{ row }"><el-tag :type="roleType(row.role)" size="small">{{ roleLabel(row.role) }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag v-if="row.valid" type="success" size="small">有效</el-tag>
              <el-tooltip v-else :content="row.error" placement="top">
                <el-tag type="danger" size="small">无效</el-tag>
              </el-tooltip>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 步骤3：导入结果 -->
      <div v-if="batchStep === 2">
        <el-result
          v-if="batchResult"
          :icon="batchResult.failed > 0 ? 'warning' : 'success'"
          :title="`导入完成`"
          :sub-title="`成功 ${batchResult.success} 条，失败 ${batchResult.failed} 条`"
        >
          <template #extra>
            <div v-if="batchResult.errors?.length" style="text-align: left; max-height: 200px; overflow-y: auto; margin-bottom: 16px">
              <p v-for="(err, i) in batchResult.errors" :key="i" style="color: #DC2626; font-size: 13px; margin: 4px 0">{{ err }}</p>
            </div>
            <el-button type="primary" @click="addBatchVisible = false">完成</el-button>
          </template>
        </el-result>
      </div>

      <template #footer>
        <el-button v-if="batchStep < 2" @click="addBatchVisible = false">取消</el-button>
        <el-button v-if="batchStep === 0" type="primary" @click="parseFile" :loading="parsingFile" :disabled="!selectedFile">
          下一步
        </el-button>
        <el-button v-if="batchStep === 1" @click="batchStep = 0">上一步</el-button>
        <el-button v-if="batchStep === 1" type="primary" @click="submitBatchImport" :loading="batchImportLoading" :disabled="selectedUsers.length === 0">
          导入 {{ selectedUsers.length }} 个用户
        </el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Upload, Download } from '@element-plus/icons-vue'
import { getUsers, updateUser, updateUserStatus, resetPassword, createUser, batchCreateUsers, downloadUserTemplate, parseUserFile } from '../api/users'
import { getDepartmentsFlat } from '../api/departments'

const loading = ref(false)
const users = ref([])
const page = ref(1)
const total = ref(0)
const statusFilter = ref('')
const editVisible = ref(false)
const editId = ref(null)
const editForm = reactive({ real_name: '', email: '', role: 'employee', department_id: null })
const departments = ref([])

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

// 批量导入
const addBatchVisible = ref(false)
const batchStep = ref(0)
const selectedFile = ref(null)
const parsingFile = ref(false)
const previewUsers = ref([])
const selectedUsers = ref([])
const batchImportLoading = ref(false)
const batchResult = ref(null)
const uploadRef = ref(null)

function getDeptName(deptId) {
  if (!deptId) return '未分配'
  const dept = departments.value.find(d => d.id === deptId)
  return dept ? dept.name : '未知'
}

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
  Object.assign(editForm, { real_name: row.real_name, email: row.email, role: row.role, department_id: row.department_id })
  editVisible.value = true
  fetchDepartments()
}

async function fetchDepartments() {
  try {
    const res = await getDepartmentsFlat()
    departments.value = res.data || []
  } catch (e) {}
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

// 批量导入用户
function showAddBatch() {
  batchStep.value = 0
  selectedFile.value = null
  previewUsers.value = []
  selectedUsers.value = []
  batchResult.value = null
  addBatchVisible.value = true
  // 清空上传组件
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

async function downloadTemplate() {
  try {
    const token = localStorage.getItem('token')
    const response = await fetch('/api/v1/users/template', {
      headers: { 'Authorization': `Bearer ${token}` }
    })

    if (!response.ok) {
      throw new Error('下载失败')
    }

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'user_template.csv'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('模板下载成功')
  } catch (e) {
    ElMessage.error('模板下载失败')
  }
}

function handleFileChange(file) {
  selectedFile.value = file.raw
}

function handleFileRemove() {
  selectedFile.value = null
}

async function parseFile() {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }

  parsingFile.value = true
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    const res = await parseUserFile(formData)
    previewUsers.value = res.data?.users || []
    // 默认全选有效用户
    selectedUsers.value = previewUsers.value.filter(u => u.valid)
    batchStep.value = 1
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '文件解析失败')
  } finally {
    parsingFile.value = false
  }
}

function handleSelectionChange(selection) {
  selectedUsers.value = selection
}

function selectAllUsers() {
  selectedUsers.value = previewUsers.value.filter(u => u.valid)
}

function deselectAllUsers() {
  selectedUsers.value = []
}

async function submitBatchImport() {
  if (selectedUsers.value.length === 0) {
    ElMessage.warning('请至少选择一个用户')
    return
  }

  batchImportLoading.value = true
  try {
    const usersToImport = selectedUsers.value.map(u => ({
      username: u.username,
      real_name: u.real_name,
      email: u.email,
      role: u.role,
      password: '123456'
    }))
    const res = await batchCreateUsers({ users: usersToImport })
    batchResult.value = res.data
    batchStep.value = 2
    fetchData()
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '导入失败')
  } finally {
    batchImportLoading.value = false
  }
}

onMounted(() => {
  fetchData()
  fetchDepartments()
})
</script>
