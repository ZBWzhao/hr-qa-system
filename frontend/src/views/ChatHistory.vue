<template>
  <el-card>
    <template #header><span style="font-weight: 600; color: #111827">问答历史</span></template>
    <div style="display: flex; gap: 12px; margin-bottom: 16px">
      <el-input v-model="keyword" placeholder="搜索问题或回答..." clearable style="width: 300px" @keyup.enter="fetchData" />
      <el-button type="primary" @click="fetchData">搜索</el-button>
      <el-checkbox v-model="onlyFavorite" @change="fetchData">仅收藏</el-checkbox>
    </div>
    <el-table :data="records" v-loading="loading" stripe>
      <el-table-column prop="question" label="问题" min-width="250" show-overflow-tooltip />
      <el-table-column prop="answer_type" label="回答类型" width="100">
        <template #default="{ row }"><el-tag size="small">{{ answerTypeLabel(row.answer_type) }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="is_favorite" label="收藏" width="80">
        <template #default="{ row }"><el-icon :color="row.is_favorite ? '#f5a623' : '#ccc'" style="cursor: pointer" @click="handleFav(row)"><Star /></el-icon></template>
      </el-table-column>
      <el-table-column prop="created_at" label="时间" width="120">
        <template #default="{ row }">{{ row.created_at?.substring(0, 10) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button size="small" @click="viewDetail(row)">详情</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination style="margin-top: 16px; justify-content: center" :current-page="page" :page-size="20" :total="total" layout="prev, pager, next" @current-change="p => { page = p; fetchData() }" />

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
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Star } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getChatHistory, toggleFavorite, deleteHistory } from '../api/chatHistory'

const loading = ref(false)
const records = ref([])
const page = ref(1)
const total = ref(0)
const keyword = ref('')
const onlyFavorite = ref(false)
const detailVisible = ref(false)
const detail = ref({})

function answerTypeLabel(t) { return { faq: 'FAQ', rule: '规则', rag: 'RAG', miss: '未命中', mock: '未命中' }[t] || t || '—' }

async function fetchData() {
  loading.value = true
  try {
    const params = { page: page.value }
    const kw = keyword.value?.trim()
    if (kw) params.keyword = kw
    if (onlyFavorite.value) params.is_favorite = 1
    const res = await getChatHistory(params)
    records.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch (e) {} finally { loading.value = false }
}

function viewDetail(row) { detail.value = row; detailVisible.value = true }

async function handleFav(row) {
  try {
    const res = await toggleFavorite(row.id)
    row.is_favorite = res.data.is_favorite
    ElMessage.success(row.is_favorite ? '已收藏' : '已取消收藏')
  } catch (e) {}
}

async function handleDelete(row) {
  await ElMessageBox.confirm('确认删除？', '提示', { type: 'warning' })
  await deleteHistory(row.id)
  ElMessage.success('删除成功')
  fetchData()
}

onMounted(() => fetchData())
</script>
