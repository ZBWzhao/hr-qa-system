<template>
  <div>
    <!-- 顶部个人信息卡片 -->
    <el-card style="margin-bottom: 16px">
      <div style="display: flex; align-items: center; gap: 16px">
        <el-avatar :size="48" style="background: #D97706; color: #fff; font-size: 20px">
          {{ userStore.userInfo.real_name?.[0] || 'U' }}
        </el-avatar>
        <div>
          <div style="font-size: 18px; font-weight: 600; color: #111827">{{ userStore.userInfo.real_name || '用户' }}</div>
          <div style="font-size: 13px; color: #9CA3AF; margin-top: 4px">
            工号：{{ userStore.userInfo.employee_id || '—' }} · {{ userStore.userInfo.department_name || '未分配部门' }}
          </div>
        </div>
        <el-button style="margin-left: auto" @click="$router.push('/profile')">编辑资料</el-button>
      </div>
    </el-card>

    <!-- 功能标签页 -->
    <el-card>
      <el-tabs v-model="activeTab">
        <!-- 我的收藏 -->
        <el-tab-pane label="我的收藏" name="favorites">
          <el-table :data="favRecords" v-loading="favLoading" stripe>
            <el-table-column prop="question" label="问题" min-width="300" show-overflow-tooltip />
            <el-table-column prop="answer_type" label="类型" width="80">
              <template #default="{ row }"><el-tag size="small">{{ answerTypeLabel(row.answer_type) }}</el-tag></template>
            </el-table-column>
            <el-table-column prop="created_at" label="时间" width="110">
              <template #default="{ row }">{{ row.created_at?.substring(0, 10) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="180">
              <template #default="{ row }">
                <el-button size="small" type="primary" plain @click="viewDetail(row)">详情</el-button>
                <el-button size="small" type="danger" plain @click="handleFav(row)">取消收藏</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-pagination style="margin-top: 16px; justify-content: center" :current-page="favPage" :page-size="20" :total="favTotal" layout="prev, pager, next" @current-change="p => { favPage = p; fetchFavorites() }" />
        </el-tab-pane>

        <!-- 我的反馈 -->
        <el-tab-pane label="我的反馈" name="feedback">
          <el-table :data="feedbacks" v-loading="feedbackLoading" stripe>
            <el-table-column prop="question" label="反馈问题" min-width="200" show-overflow-tooltip />
            <el-table-column prop="feedback_type" label="类型" width="80">
              <template #default="{ row }"><el-tag :type="row.feedback_type === 'useful' ? 'success' : 'danger'" size="small">{{ row.feedback_type === 'useful' ? '有用' : '无用' }}</el-tag></template>
            </el-table-column>
            <el-table-column prop="correction_text" label="纠错内容" min-width="200" show-overflow-tooltip>
              <template #default="{ row }">{{ row.correction_text || '—' }}</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }"><el-tag :type="feedbackStatusType(row.status)" size="small">{{ feedbackStatusLabel(row.status) }}</el-tag></template>
            </el-table-column>
            <el-table-column prop="created_at" label="时间" width="110">
              <template #default="{ row }">{{ row.created_at?.substring(0, 10) }}</template>
            </el-table-column>
          </el-table>
          <el-pagination style="margin-top: 16px; justify-content: center" :current-page="feedbackPage" :page-size="20" :total="feedbackTotal" layout="prev, pager, next" @current-change="p => { feedbackPage = p; fetchFeedbacks() }" />
        </el-tab-pane>

        <!-- 人工请求 -->
        <el-tab-pane label="人工请求" name="tickets">
          <div style="margin-bottom: 16px">
            <el-button type="primary" @click="showCreateTicket">创建请求</el-button>
          </div>
          <el-table :data="tickets" v-loading="ticketLoading" stripe>
            <el-table-column prop="ticket_no" label="编号" width="130" />
            <el-table-column prop="title" label="标题" min-width="200" />
            <el-table-column prop="type" label="类型" width="90">
              <template #default="{ row }"><el-tag size="small">{{ ticketTypeLabel(row.type) }}</el-tag></template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }"><el-tag :type="ticketStatusType(row.status)" size="small">{{ ticketStatusLabel(row.status) }}</el-tag></template>
            </el-table-column>
            <el-table-column prop="created_at" label="时间" width="110">
              <template #default="{ row }">{{ row.created_at?.substring(0, 10) }}</template>
            </el-table-column>
          </el-table>
          <el-pagination style="margin-top: 16px; justify-content: center" :current-page="ticketPage" :page-size="20" :total="ticketTotal" layout="prev, pager, next" @current-change="p => { ticketPage = p; fetchTickets() }" />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 问答详情抽屉 -->
    <el-drawer v-model="detailVisible" title="问答详情" size="50%">
      <h4>问题</h4>
      <p style="color: #374151">{{ detail.question }}</p>
      <el-divider />
      <h4>回答</h4>
      <div style="white-space: pre-wrap; line-height: 1.8">{{ detail.answer }}</div>
      <el-divider />
      <el-descriptions :column="2" border>
        <el-descriptions-item label="回答类型"><el-tag size="small">{{ answerTypeLabel(detail.answer_type) }}</el-tag></el-descriptions-item>
        <el-descriptions-item label="收藏状态">{{ detail.is_favorite ? '已收藏' : '未收藏' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ detail.created_at }}</el-descriptions-item>
      </el-descriptions>
      <div v-if="detail.source_docs" style="margin-top: 16px">
        <h4>来源文档</h4>
        <div style="white-space: pre-wrap; color: #6B7280; font-size: 13px">{{ detail.source_docs }}</div>
      </div>
    </el-drawer>

    <!-- 创建工单对话框 -->
    <el-dialog v-model="createTicketVisible" title="创建人工请求" width="500px">
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
        <el-button @click="createTicketVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCreateTicket">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { Star } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getChatHistory, toggleFavorite, deleteHistory } from '../api/chatHistory'
import { getFeedbacks } from '../api/feedback'
import { getTickets, createTicket } from '../api/tickets'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const activeTab = ref('favorites')

const detailVisible = ref(false)
const detail = ref({})

function answerTypeLabel(t) { return { faq: 'FAQ', rule: '规则', rag: 'RAG', miss: '未命中', mock: '未命中' }[t] || t || '—' }

function viewDetail(row) { detail.value = row; detailVisible.value = true }

async function handleFav(row) {
  try {
    const res = await toggleFavorite(row.id)
    row.is_favorite = res.data.is_favorite
    ElMessage.success(row.is_favorite ? '已收藏' : '已取消收藏')
    if (activeTab.value === 'favorites') fetchFavorites()
  } catch (e) {}
}

// ===== 我的收藏 =====
const favLoading = ref(false)
const favRecords = ref([])
const favPage = ref(1)
const favTotal = ref(0)

async function fetchFavorites() {
  favLoading.value = true
  try {
    const res = await getChatHistory({ page: favPage.value, is_favorite: 1 })
    favRecords.value = res.data?.items || []
    favTotal.value = res.data?.total || 0
  } catch (e) {} finally { favLoading.value = false }
}

// ===== 我的反馈 =====
const feedbackLoading = ref(false)
const feedbacks = ref([])
const feedbackPage = ref(1)
const feedbackTotal = ref(0)

function feedbackStatusType(s) { return { pending: 'warning', resolved: 'success', ignored: 'info' }[s] || '' }
function feedbackStatusLabel(s) { return { pending: '待处理', resolved: '已处理', ignored: '已忽略' }[s] || s }

async function fetchFeedbacks() {
  feedbackLoading.value = true
  try {
    const res = await getFeedbacks({ page: feedbackPage.value })
    feedbacks.value = res.data?.items || []
    feedbackTotal.value = res.data?.total || 0
  } catch (e) {} finally { feedbackLoading.value = false }
}

// ===== 人工请求 =====
const ticketLoading = ref(false)
const tickets = ref([])
const ticketPage = ref(1)
const ticketTotal = ref(0)
const createTicketVisible = ref(false)
const createForm = reactive({ type: 'other', title: '', description: '' })

function ticketTypeLabel(t) { return { certify: '证明开具', info_change: '信息变更', other: '其他' }[t] || t }
function ticketStatusType(s) { return { pending: 'warning', processing: 'primary', completed: 'success', rejected: 'danger' }[s] || '' }
function ticketStatusLabel(s) { return { pending: '待处理', processing: '处理中', completed: '已完成', rejected: '已驳回' }[s] || s }

async function fetchTickets() {
  ticketLoading.value = true
  try {
    const res = await getTickets({ page: ticketPage.value })
    tickets.value = res.data?.items || []
    ticketTotal.value = res.data?.total || 0
  } catch (e) {} finally { ticketLoading.value = false }
}

function showCreateTicket() { Object.assign(createForm, { type: 'other', title: '', description: '' }); createTicketVisible.value = true }

async function submitCreateTicket() {
  await createTicket(createForm)
  ElMessage.success('请求已提交')
  createTicketVisible.value = false
  fetchTickets()
}

// ===== 标签切换时加载数据 =====
watch(activeTab, (tab) => {
  if (tab === 'favorites') fetchFavorites()
  else if (tab === 'feedback') fetchFeedbacks()
  else if (tab === 'tickets') fetchTickets()
})

onMounted(() => fetchFavorites())
</script>
