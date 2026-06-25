<template>
  <el-card>
    <div style="display: flex; gap: 16px; margin-bottom: 20px">
      <el-input v-model="keyword" placeholder="输入关键词搜索制度文档..." size="large" clearable @keyup.enter="handleSearch" style="flex: 1" />
      <el-select v-model="category" placeholder="全部分类" clearable size="large" style="width: 160px">
        <el-option label="考勤" value="attendance" />
        <el-option label="薪酬" value="salary" />
        <el-option label="福利" value="benefit" />
        <el-option label="休假" value="leave" />
        <el-option label="绩效" value="performance" />
        <el-option label="其他" value="other" />
      </el-select>
      <el-button type="primary" size="large" @click="handleSearch">搜索</el-button>
    </div>

    <div v-if="searched">
      <div style="margin-bottom: 16px; color: #9CA3AF">共找到 {{ total }} 条结果</div>
      <div v-for="item in results" :key="item.chunk_id" class="result-item" @click="viewDoc(item.document_id)">
        <div class="result-title">
          <el-tag size="small" style="margin-right: 8px">{{ categoryLabel(item.category) }}</el-tag>
          {{ item.document_title }}
        </div>
        <div class="result-content" v-html="item.highlighted_content"></div>
      </div>
      <el-empty v-if="results.length === 0" description="未找到相关内容" />
      <el-pagination v-if="total > pageSize" :current-page="page" :page-size="pageSize" :total="total" layout="prev, pager, next" style="margin-top: 20px; justify-content: center" @current-change="p => { page = p; handleSearch() }" />
    </div>
  </el-card>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { searchDocuments } from '../api/search'

const router = useRouter()
const keyword = ref('')
const category = ref('')
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const results = ref([])
const searched = ref(false)

function categoryLabel(c) {
  return { attendance: '考勤', salary: '薪酬', benefit: '福利', leave: '休假', performance: '绩效', other: '其他' }[c] || c
}

async function handleSearch() {
  if (!keyword.value.trim()) return
  searched.value = true
  try {
    const res = await searchDocuments({ keyword: keyword.value, category: category.value, page: page.value, page_size: pageSize.value })
    results.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch (e) {}
}

function viewDoc(docId) {
  router.push({ path: '/documents', query: { id: docId } })
}
</script>

<style scoped>
.result-item { padding: 16px; border: 1px solid #f3f4f6; border-radius: 12px; margin-bottom: 12px; cursor: pointer; transition: all 0.3s; }
.result-item:hover { border-color: #D97706; box-shadow: 0 2px 8px rgba(217, 119, 6, 0.08); }
.result-title { font-size: 16px; font-weight: 600; color: #111827; margin-bottom: 8px; }
.result-content { color: #6B7280; font-size: 14px; line-height: 1.6; }
.result-content :deep(em) { color: #f5222d; font-style: normal; font-weight: 600; }
</style>