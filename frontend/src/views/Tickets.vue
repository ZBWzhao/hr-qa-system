<template>
  <el-card>
    <template #header>
      <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px">
        <span style="font-weight: 600; color: #111827">工单系统</span>
        <el-button type="primary" @click="showCreate">创建工单</el-button>
      </div>
    </template>
    <el-table :data="tickets" v-loading="loading" stripe>
      <el-table-column prop="ticket_no" label="工单号" width="150" />
      <el-table-column prop="title" label="标题" min-width="200" />
      <el-table-column prop="type" label="类型" width="100">
        <template #default="{ row }"><el-tag size="small">{{ row.type_label || ticketTypeLabel(row.type) }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }"><el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="120">
        <template #default="{ row }">{{ row.created_at?.substring(0, 10) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="250" v-if="userStore.isHR">
        <template #default="{ row }">
          <el-button v-if="row.status === 'pending'" size="small" type="primary" @click="handleAccept(row)">受理</el-button>
          <el-button v-if="row.status === 'processing'" size="small" type="success" @click="showComplete(row)">完成</el-button>
          <el-button v-if="row.status !== 'completed' && row.status !== 'rejected'" size="small" type="danger" @click="showReject(row)">驳回</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination style="margin-top: 16px; justify-content: center" :current-page="page" :page-size="20" :total="total" layout="prev, pager, next" @current-change="p => { page = p; fetchData() }" />

    <el-dialog v-model="createVisible" title="创建工单" width="500px">
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="类型">
          <el-select v-model="createForm.type">
            <el-option label="证明开具" value="证明开具" />
            <el-option label="信息变更" value="信息变更" />
            <el-option label="考勤异常" value="考勤异常" />
            <el-option label="请假申请" value="请假申请" />
            <el-option label="离职申请" value="离职申请" />
            <el-option label="入职/转正" value="入职转正" />
            <el-option label="报销/薪资" value="报销薪资" />
            <el-option label="其他" value="其他" />
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
        <el-form-item label="处理备注"><el-input v-model="resolveNote" type="textarea" :rows="4" placeholder="请填写处理备注" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="completeVisible = false">取消</el-button>
        <el-button type="primary" @click="submitComplete">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="rejectVisible" title="驳回工单" width="500px">
      <el-form label-width="80px">
        <el-form-item label="驳回原因"><el-input v-model="rejectNote" type="textarea" :rows="4" placeholder="请填写驳回原因" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rejectVisible = false">取消</el-button>
        <el-button type="primary" @click="submitReject">确定驳回</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getTickets, createTicket, updateTicket } from '../api/tickets'
import { ticketTypeLabel, ticketStatusLabel, ticketStatusType } from '../utils/ticketLabels'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const loading = ref(false)
const tickets = ref([])
const page = ref(1)
const total = ref(0)
const createVisible = ref(false)
const createForm = reactive({ type: 'other', title: '', description: '' })
const completeVisible = ref(false)
const rejectVisible = ref(false)
const currentId = ref(null)
const resolveNote = ref('')
const rejectNote = ref('')

function typeLabel(t) { return ticketTypeLabel(t) }
function statusType(s) { return ticketStatusType(s) }
function statusLabel(s) { return ticketStatusLabel(s) }

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

async function handleAccept(row) {
  await ElMessageBox.confirm('确认受理该工单？', '提示', { type: 'info' })
  await updateTicket(row.id, { status: 'processing' })
  ElMessage.success('已受理')
  fetchData()
}

function showComplete(row) { currentId.value = row.id; resolveNote.value = ''; completeVisible.value = true }

async function submitComplete() {
  if (!resolveNote.value.trim()) {
    ElMessage.warning('请填写处理备注')
    return
  }
  await updateTicket(currentId.value, { status: 'completed', resolve_note: resolveNote.value })
  ElMessage.success('工单已完成')
  completeVisible.value = false
  fetchData()
}

function showReject(row) { currentId.value = row.id; rejectNote.value = ''; rejectVisible.value = true }

async function submitReject() {
  if (!rejectNote.value.trim()) {
    ElMessage.warning('请填写驳回原因')
    return
  }
  await updateTicket(currentId.value, { status: 'rejected', resolve_note: rejectNote.value })
  ElMessage.success('工单已驳回')
  rejectVisible.value = false
  fetchData()
}

onMounted(() => fetchData())
</script>
