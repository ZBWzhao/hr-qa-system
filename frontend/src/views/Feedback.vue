<template>
  <el-card>
    <template #header><span style="font-weight: 600; color: #111827">反馈纠错</span></template>
    <el-table :data="feedbacks" v-loading="loading" stripe>
      <el-table-column prop="question" label="反馈问题" min-width="200" show-overflow-tooltip />
      <el-table-column prop="answer_type" label="回答类型" width="100">
        <template #default="{ row }"><el-tag size="small">{{ answerTypeLabel(row.answer_type) }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="feedback_type" label="反馈类型" width="100">
        <template #default="{ row }"><el-tag :type="row.feedback_type === 'useful' ? 'success' : 'danger'" size="small">{{ row.feedback_type === 'useful' ? '有用' : '无用' }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="correction_text" label="纠错内容" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">
          <span v-if="row.feedback_type === 'useful'">—</span>
          <span v-else>{{ row.correction_text || '仅评价为无用，未填写纠错说明' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="user_name" label="反馈人" width="100" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }"><el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="created_at" label="提交时间" width="120">
        <template #default="{ row }">{{ row.created_at?.substring(0, 10) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="150" v-if="userStore.isHR">
        <template #default="{ row }">
          <el-button v-if="row.status === 'pending'" size="small" type="primary" @click="showHandle(row)">处理</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination style="margin-top: 16px; justify-content: center" :current-page="page" :page-size="20" :total="total" layout="prev, pager, next" @current-change="p => { page = p; fetchData() }" />

    <el-dialog v-model="handleVisible" title="处理反馈" width="600px">
      <div style="margin-bottom: 16px">
        <h4 style="margin-bottom: 8px">原问题</h4>
        <p style="color: #374151; background: #f9fafb; padding: 12px; border-radius: 8px">{{ currentFeedback.question || '—' }}</p>
        <h4 style="margin: 12px 0 8px">原回答</h4>
        <p style="color: #374151; background: #f9fafb; padding: 12px; border-radius: 8px; white-space: pre-wrap">{{ currentFeedback.answer || '—' }}</p>
        <h4 style="margin: 12px 0 8px">纠错说明</h4>
        <p style="color: #374151; background: #f9fafb; padding: 12px; border-radius: 8px">
          <span v-if="currentFeedback.feedback_type === 'useful'">—</span>
          <span v-else>{{ currentFeedback.correction_text || '仅评价为无用，未填写纠错说明' }}</span>
        </p>
      </div>
      <el-form :model="handleForm" label-width="80px">
        <el-form-item label="处理状态">
          <el-select v-model="handleForm.status">
            <el-option label="已处理" value="resolved" />
            <el-option label="已忽略" value="ignored" />
          </el-select>
        </el-form-item>
        <el-form-item label="处理说明"><el-input v-model="handleForm.handle_note" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="handleVisible = false">取消</el-button>
        <el-button type="primary" @click="submitHandle">确定</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getFeedbacks, handleFeedback } from '../api/feedback'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const loading = ref(false)
const feedbacks = ref([])
const page = ref(1)
const total = ref(0)
const handleVisible = ref(false)
const currentId = ref(null)
const currentFeedback = ref({})
const handleForm = reactive({ status: 'resolved', handle_note: '' })

function statusType(s) { return { pending: 'warning', resolved: 'success', ignored: 'info' }[s] || '' }
function statusLabel(s) { return { pending: '待处理', resolved: '已处理', ignored: '已忽略' }[s] || s }
function answerTypeLabel(t) { return { faq: 'FAQ', rule: '规则', rag: 'RAG', miss: '未命中', mock: '未命中' }[t] || t || '—' }

async function fetchData() {
  loading.value = true
  try {
    const res = await getFeedbacks({ page: page.value })
    feedbacks.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch (e) {} finally { loading.value = false }
}

function showHandle(row) {
  currentId.value = row.id
  currentFeedback.value = row
  handleForm.status = 'resolved'
  handleForm.handle_note = ''
  handleVisible.value = true
}

async function submitHandle() {
  await handleFeedback(currentId.value, handleForm)
  ElMessage.success('处理成功')
  handleVisible.value = false
  fetchData()
}

onMounted(() => fetchData())
</script>
