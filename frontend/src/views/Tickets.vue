<template>
  <el-card>
    <template #header>
      <div style="display: flex; justify-content: space-between; align-items: center">
        <span style="font-weight: 600; color: #111827">工单系统</span>
        <el-button type="primary" @click="showCreate">创建工单</el-button>
      </div>
    </template>
    <el-table :data="tickets" v-loading="loading" stripe>
      <el-table-column prop="ticket_no" label="工单号" width="150" />
      <el-table-column prop="title" label="标题" min-width="200" />
      <el-table-column prop="type" label="类型" width="100">
        <template #default="{ row }"><el-tag size="small">{{ typeLabel(row.type) }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }"><el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="120">
        <template #default="{ row }">{{ row.created_at?.substring(0, 10) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="250" v-if="userStore.isHR">
        <template #default="{ row }">
          <el-button v-if="row.status === 'pending'" size="small" type="primary" @click="handleStatus(row, 'processing')">受理</el-button>
          <el-button v-if="row.status === 'processing'" size="small" type="success" @click="showComplete(row)">完成</el-button>
          <el-button v-if="row.status !== 'completed' && row.status !== 'rejected'" size="small" type="danger" @click="handleStatus(row, 'rejected')">驳回</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination style="margin-top: 16px; justify-content: center" :current-page="page" :page-size="20" :total="total" layout="prev, pager, next" @current-change="p => { page = p; fetchData() }" />

    <el-dialog v-model="createVisible" title="创建工单" width="500px">
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="类型">
          <el-select v-model="createForm.type">
            <el-option label="证明开具" value="certify" />
            <el-option label="信息变更" value="info_change" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题"><el-input v-model="createForm.title" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="createForm.description" type="textarea" :rows="4" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCreate">提交</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="completeVisible" title="完成工单" width="500px">
      <el-form label-width="80px">
        <el-form-item label="处理备注"><el-input v-model="resolveNote" type="textarea" :rows="4" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="completeVisible = false">取消</el-button>
        <el-button type="primary" @click="submitComplete">确定</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getTickets, createTicket, updateTicket } from '../api/tickets'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const loading = ref(false)
const tickets = ref([])
const page = ref(1)
const total = ref(0)
const createVisible = ref(false)
const createForm = reactive({ type: 'other', title: '', description: '' })
const completeVisible = ref(false)
const currentId = ref(null)
const resolveNote = ref('')

function typeLabel(t) { return { certify: '证明开具', info_change: '信息变更', other: '其他' }[t] || t }
function statusType(s) { return { pending: 'warning', processing: 'primary', completed: 'success', rejected: 'danger' }[s] || '' }
function statusLabel(s) { return { pending: '待处理', processing: '处理中', completed: '已完成', rejected: '已驳回' }[s] || s }

async function fetchData() {
  loading.value = true
  try {
    const res = await getTickets({ page: page.value })
    tickets.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch (e) {} finally { loading.value = false }
}

function showCreate() { Object.assign(createForm, { type: 'other', title: '', description: '' }); createVisible.value = true }

async function submitCreate() {
  await createTicket(createForm)
  ElMessage.success('工单创建成功')
  createVisible.value = false
  fetchData()
}

async function handleStatus(row, status) {
  await updateTicket(row.id, { status })
  ElMessage.success('操作成功')
  fetchData()
}

function showComplete(row) { currentId.value = row.id; resolveNote.value = ''; completeVisible.value = true }

async function submitComplete() {
  await updateTicket(currentId.value, { status: 'completed', resolve_note: resolveNote.value })
  ElMessage.success('工单已完成')
  completeVisible.value = false
  fetchData()
}

onMounted(() => fetchData())
</script>