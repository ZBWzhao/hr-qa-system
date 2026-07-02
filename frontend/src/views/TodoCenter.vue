<template>
  <el-card>
    <template #header>
      <div style="display: flex; justify-content: space-between; align-items: center">
        <span style="font-weight: 600; color: #111827">待办中心</span>
        <div style="display: flex; gap: 12px">
          <el-badge :value="pendingTickets" :hidden="pendingTickets === 0" :max="99">
            <el-tag :type="activeTab === 'tickets' ? '' : 'info'" style="cursor: pointer" @click="activeTab = 'tickets'">工单</el-tag>
          </el-badge>
          <el-badge :value="pendingFeedbacks" :hidden="pendingFeedbacks === 0" :max="99">
            <el-tag :type="activeTab === 'feedback' ? '' : 'info'" style="cursor: pointer" @click="activeTab = 'feedback'">反馈</el-tag>
          </el-badge>
          <el-badge :value="unresolvedGaps" :hidden="unresolvedGaps === 0" :max="99">
            <el-tag :type="activeTab === 'gaps' ? '' : 'info'" style="cursor: pointer" @click="activeTab = 'gaps'">缺口</el-tag>
          </el-badge>
        </div>
      </div>
    </template>

    <el-tabs v-model="activeTab">
      <!-- 工单管理 -->
      <el-tab-pane label="工单管理" name="tickets">
        <div style="display: flex; gap: 12px; margin-bottom: 16px">
          <el-select v-model="ticketStatusFilter" placeholder="全部状态" clearable @change="fetchTickets" style="width: 160px">
            <el-option label="待处理" value="pending" />
            <el-option label="处理中" value="processing" />
            <el-option label="已完成" value="completed" />
            <el-option label="已驳回" value="rejected" />
          </el-select>
        </div>
        <el-table :data="tickets" v-loading="ticketLoading" stripe>
          <el-table-column prop="ticket_no" label="工单号" width="130" />
          <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
          <el-table-column prop="type" label="类型" width="90">
            <template #default="{ row }"><el-tag size="small">{{ ticketTypeLabel(row.type) }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }"><el-tag :type="ticketStatusType(row.status)" size="small">{{ ticketStatusLabel(row.status) }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="110">
            <template #default="{ row }">{{ row.created_at?.substring(0, 10) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <template v-if="row.status === 'pending'">
                <el-button size="small" type="success" @click="handleTicket(row, 'processing')">受理</el-button>
                <el-button size="small" type="danger" @click="showRejectTicket(row)">驳回</el-button>
              </template>
              <template v-else-if="row.status === 'processing'">
                <el-button size="small" type="primary" @click="showCompleteTicket(row)">完成</el-button>
              </template>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination style="margin-top: 16px; justify-content: center" :current-page="ticketPage" :page-size="20" :total="ticketTotal" layout="prev, pager, next" @current-change="p => { ticketPage = p; fetchTickets() }" />
      </el-tab-pane>

      <!-- 反馈处理 -->
      <el-tab-pane label="反馈处理" name="feedback">
        <el-table :data="feedbacks" v-loading="feedbackLoading" stripe>
          <el-table-column prop="question" label="反馈问题" min-width="200" show-overflow-tooltip />
          <el-table-column prop="answer_type" label="回答类型" width="80">
            <template #default="{ row }"><el-tag size="small">{{ answerTypeLabel(row.answer_type) }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="feedback_type" label="反馈类型" width="80">
            <template #default="{ row }"><el-tag :type="row.feedback_type === 'useful' ? 'success' : 'danger'" size="small">{{ row.feedback_type === 'useful' ? '有用' : '无用' }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="correction_text" label="纠错内容" min-width="180" show-overflow-tooltip>
            <template #default="{ row }">
              <span v-if="row.feedback_type === 'useful'">—</span>
              <span v-else>{{ row.correction_text || '未填写' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="user_name" label="反馈人" width="80" />
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }"><el-tag :type="feedbackStatusType(row.status)" size="small">{{ feedbackStatusLabel(row.status) }}</el-tag></template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button v-if="row.status === 'pending'" size="small" type="primary" @click="showHandleFeedback(row)">处理</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination style="margin-top: 16px; justify-content: center" :current-page="feedbackPage" :page-size="20" :total="feedbackTotal" layout="prev, pager, next" @current-change="p => { feedbackPage = p; fetchFeedbacks() }" />
      </el-tab-pane>

      <!-- 知识缺口 -->
      <el-tab-pane label="知识缺口" name="gaps">
        <el-table :data="gaps" v-loading="gapLoading" stripe>
          <el-table-column prop="question" label="未命中问题" min-width="300" show-overflow-tooltip />
          <el-table-column prop="user_name" label="提问人" width="100" />
          <el-table-column prop="resolved" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.resolved ? 'success' : 'warning'" size="small">{{ row.resolved ? '已解决' : '未解决' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="记录时间" width="120">
            <template #default="{ row }">{{ row.created_at?.substring(0, 10) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button v-if="!row.resolved" size="small" type="success" @click="resolveGap(row)">标记已解决</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination style="margin-top: 16px; justify-content: center" :current-page="gapPage" :page-size="20" :total="gapTotal" layout="prev, pager, next" @current-change="p => { gapPage = p; fetchGaps() }" />
      </el-tab-pane>
    </el-tabs>

    <!-- 完成工单对话框 -->
    <el-dialog v-model="completeVisible" title="完成工单" width="500px">
      <el-form label-width="80px">
        <el-form-item label="处理备注">
          <el-input v-model="completeNote" type="textarea" :rows="4" placeholder="请输入处理备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="completeVisible = false">取消</el-button>
        <el-button type="primary" @click="submitComplete">确定</el-button>
      </template>
    </el-dialog>

    <!-- 驳回工单对话框 -->
    <el-dialog v-model="rejectVisible" title="驳回工单" width="500px">
      <el-form label-width="80px">
        <el-form-item label="驳回原因">
          <el-input v-model="rejectReason" type="textarea" :rows="4" placeholder="请输入驳回原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rejectVisible = false">取消</el-button>
        <el-button type="danger" @click="submitReject">确定驳回</el-button>
      </template>
    </el-dialog>

    <!-- 处理反馈对话框 -->
    <el-dialog v-model="handleFeedbackVisible" title="处理反馈" width="600px">
      <div style="margin-bottom: 16px">
        <h4 style="margin-bottom: 8px">原问题</h4>
        <p style="color: #374151; background: #f9fafb; padding: 12px; border-radius: 8px">{{ currentFeedback.question || '—' }}</p>
        <h4 style="margin: 12px 0 8px">原回答</h4>
        <p style="color: #374151; background: #f9fafb; padding: 12px; border-radius: 8px; white-space: pre-wrap">{{ currentFeedback.answer || '—' }}</p>
        <h4 style="margin: 12px 0 8px">纠错说明</h4>
        <p style="color: #374151; background: #f9fafb; padding: 12px; border-radius: 8px">
          <span v-if="currentFeedback.feedback_type === 'useful'">—</span>
          <span v-else>{{ currentFeedback.correction_text || '未填写' }}</span>
        </p>
      </div>
      <el-form label-width="80px">
        <el-form-item label="处理状态">
          <el-select v-model="handleFeedbackForm.status">
            <el-option label="已处理" value="resolved" />
            <el-option label="已忽略" value="ignored" />
          </el-select>
        </el-form-item>
        <el-form-item label="处理说明">
          <el-input v-model="handleFeedbackForm.handle_note" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="handleFeedbackVisible = false">取消</el-button>
        <el-button type="primary" @click="submitHandleFeedback">确定</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getTickets, updateTicket, getTicketStats } from '../api/tickets'
import { getFeedbacks, handleFeedback } from '../api/feedback'
import { getGaps, resolveGap as resolveGapApi } from '../api/gaps'

const activeTab = ref('tickets')

// 工单相关
const ticketLoading = ref(false)
const tickets = ref([])
const ticketPage = ref(1)
const ticketTotal = ref(0)
const ticketStatusFilter = ref('')
const pendingTickets = ref(0)
const completeVisible = ref(false)
const rejectVisible = ref(false)
const currentTicketId = ref(null)
const completeNote = ref('')
const rejectReason = ref('')

// 反馈相关
const feedbackLoading = ref(false)
const feedbacks = ref([])
const feedbackPage = ref(1)
const feedbackTotal = ref(0)
const pendingFeedbacks = ref(0)
const handleFeedbackVisible = ref(false)
const currentFeedback = ref({})
const handleFeedbackForm = reactive({ status: 'resolved', handle_note: '' })

// 知识缺口相关
const gapLoading = ref(false)
const gaps = ref([])
const gapPage = ref(1)
const gapTotal = ref(0)
const unresolvedGaps = ref(0)

// 工单相关函数
function ticketTypeLabel(t) { return { certify: '证明开具', info_change: '信息变更', other: '其他' }[t] || t }
function ticketStatusType(s) { return { pending: 'warning', processing: 'primary', completed: 'success', rejected: 'danger' }[s] || '' }
function ticketStatusLabel(s) { return { pending: '待处理', processing: '处理中', completed: '已完成', rejected: '已驳回' }[s] || s }

async function fetchTickets() {
  ticketLoading.value = true
  try {
    const params = { page: ticketPage.value }
    if (ticketStatusFilter.value) params.status = ticketStatusFilter.value
    const res = await getTickets(params)
    tickets.value = res.data?.items || []
    ticketTotal.value = res.data?.total || 0
  } catch (e) {} finally { ticketLoading.value = false }
}

async function fetchTicketStats() {
  try {
    const res = await getTicketStats()
    pendingTickets.value = res.data?.pending || 0
  } catch (e) {}
}

async function handleTicket(row, status) {
  await updateTicket(row.id, { status })
  ElMessage.success('操作成功')
  fetchTickets()
  fetchTicketStats()
}

function showCompleteTicket(row) {
  currentTicketId.value = row.id
  completeNote.value = ''
  completeVisible.value = true
}

async function submitComplete() {
  await updateTicket(currentTicketId.value, { status: 'completed', handle_note: completeNote.value })
  ElMessage.success('工单已完成')
  completeVisible.value = false
  fetchTickets()
  fetchTicketStats()
}

function showRejectTicket(row) {
  currentTicketId.value = row.id
  rejectReason.value = ''
  rejectVisible.value = true
}

async function submitReject() {
  if (!rejectReason.value.trim()) {
    ElMessage.warning('请输入驳回原因')
    return
  }
  await updateTicket(currentTicketId.value, { status: 'rejected', handle_note: rejectReason.value })
  ElMessage.success('工单已驳回')
  rejectVisible.value = false
  fetchTickets()
  fetchTicketStats()
}

// 反馈相关函数
function answerTypeLabel(t) { return { faq: 'FAQ', rule: '规则', rag: 'RAG', miss: '未命中' }[t] || t || '—' }
function feedbackStatusType(s) { return { pending: 'warning', resolved: 'success', ignored: 'info' }[s] || '' }
function feedbackStatusLabel(s) { return { pending: '待处理', resolved: '已处理', ignored: '已忽略' }[s] || s }

async function fetchFeedbacks() {
  feedbackLoading.value = true
  try {
    const res = await getFeedbacks({ page: feedbackPage.value })
    feedbacks.value = res.data?.items || []
    feedbackTotal.value = res.data?.total || 0
    pendingFeedbacks.value = feedbacks.value.filter(f => f.status === 'pending').length
  } catch (e) {} finally { feedbackLoading.value = false }
}

function showHandleFeedback(row) {
  currentFeedback.value = row
  handleFeedbackForm.status = 'resolved'
  handleFeedbackForm.handle_note = ''
  handleFeedbackVisible.value = true
}

async function submitHandleFeedback() {
  await handleFeedback(currentFeedback.value.id, handleFeedbackForm)
  ElMessage.success('处理成功')
  handleFeedbackVisible.value = false
  fetchFeedbacks()
}

// 知识缺口相关函数
async function fetchGaps() {
  gapLoading.value = true
  try {
    const res = await getGaps({ page: gapPage.value })
    gaps.value = res.data?.items || []
    gapTotal.value = res.data?.total || 0
    unresolvedGaps.value = gaps.value.filter(g => !g.resolved).length
  } catch (e) {} finally { gapLoading.value = false }
}

async function resolveGap(row) {
  await ElMessageBox.confirm('确认将此问题标记为已解决？', '提示')
  await resolveGapApi(row.id)
  ElMessage.success('已标记为已解决')
  fetchGaps()
}

// 标签切换时加载数据
watch(activeTab, (tab) => {
  if (tab === 'tickets') fetchTickets()
  else if (tab === 'feedback') fetchFeedbacks()
  else if (tab === 'gaps') fetchGaps()
})

onMounted(() => {
  fetchTickets()
  fetchTicketStats()
})
</script>
