<template>
  <el-card>
    <div style="display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap">
      <el-input v-model="keyword" placeholder="输入关键词搜索制度文档..." size="large" clearable @keyup.enter="handleSearch" style="flex: 1; min-width: 160px" />
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

    <div v-if="!searched">
      <div class="hot-search">
        <h3 style="color: #374151; margin-bottom: 16px">热门搜索</h3>
        <div style="display: flex; flex-wrap: wrap; gap: 8px; justify-content: center">
          <el-tag v-for="q in hotQuestions" :key="q" effect="plain" style="cursor: pointer" @click="searchHot(q)">{{ q }}</el-tag>
        </div>
      </div>

      <div style="margin-top: 32px">
        <h3 style="color: #374151; margin-bottom: 16px">全部制度文档</h3>
        <div class="doc-grid">
          <div v-for="doc in allDocs" :key="doc.id" class="doc-card" @click="viewDoc(doc.id)">
            <div class="doc-card-header">
              <el-tag size="small" :type="categoryType(doc.category)">{{ categoryLabel(doc.category) }}</el-tag>
              <span class="doc-version">v{{ doc.version }}</span>
            </div>
            <div class="doc-card-title">{{ doc.title }}</div>
            <div class="doc-card-meta">
              <span>{{ doc.uploader_name || '—' }}</span>
              <span>{{ doc.updated_at?.substring(0, 10) }}</span>
            </div>
          </div>
        </div>
        <el-empty v-if="allDocs.length === 0" description="暂无已发布文档" />
      </div>
    </div>

    <div v-if="searched">
      <div style="margin-bottom: 16px; color: #9CA3AF; display: flex; justify-content: space-between; align-items: center">
        <span>共找到 {{ total }} 条结果</span>
        <el-button text type="primary" @click="searched = false">返回全部文档</el-button>
      </div>
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { searchDocuments } from '../api/search'
import { getDocuments } from '../api/documents'

const router = useRouter()
const keyword = ref('')
const category = ref('')
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const results = ref([])
const searched = ref(false)
const allDocs = ref([])
const hotQuestions = ['年假怎么计算？', '请假需要提前多久？', '加班可以调休吗？', '试用期多久？', '报销流程是什么？']

function categoryLabel(c) {
  return { attendance: '考勤', salary: '薪酬', benefit: '福利', leave: '休假', performance: '绩效', other: '其他' }[c] || c
}

function categoryType(c) {
  return { attendance: '', salary: 'success', benefit: 'warning', leave: 'primary', performance: 'danger', other: 'info' }[c] || ''
}

function searchHot(q) {
  keyword.value = q
  handleSearch()
}

async function handleSearch() {
  const kw = keyword.value?.trim()
  if (!kw) return
  searched.value = true
  try {
    const res = await searchDocuments({ keyword: kw, category: category.value, page: page.value, page_size: pageSize.value })
    results.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch (e) {}
}

async function fetchAllDocs() {
  try {
    const res = await getDocuments({ page: 1, page_size: 100, status: 'published' })
    allDocs.value = res.data?.items || []
  } catch (e) {}
}

function viewDoc(docId) {
  router.push({ path: '/documents', query: { id: docId } })
}

onMounted(() => {
  fetchAllDocs()
})
</script>

<style scoped>
.hot-search { text-align: center; padding: 40px 0 20px; }
.doc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}
.doc-card {
  padding: 16px;
  border: 1px solid #f3f4f6;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  background: #fff;
}
.doc-card:hover {
  border-color: #D97706;
  box-shadow: 0 2px 12px rgba(217, 119, 6, 0.1);
  transform: translateY(-2px);
}
.doc-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.doc-version {
  color: #9CA3AF;
  font-size: 12px;
}
.doc-card-title {
  font-size: 15px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 10px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.doc-card-meta {
  display: flex;
  justify-content: space-between;
  color: #9CA3AF;
  font-size: 12px;
}
.result-item { padding: 16px; border: 1px solid #f3f4f6; border-radius: 12px; margin-bottom: 12px; cursor: pointer; transition: all 0.3s; }
.result-item:hover { border-color: #D97706; box-shadow: 0 2px 8px rgba(217, 119, 6, 0.08); }
.result-title { font-size: 16px; font-weight: 600; color: #111827; margin-bottom: 8px; }
.result-content { color: #6B7280; font-size: 14px; line-height: 1.6; }
.result-content :deep(em) { color: #f5222d; font-style: normal; font-weight: 600; }

@media (max-width: 768px) {
  .doc-grid {
    grid-template-columns: 1fr;
  }
  .hot-search {
    padding: 20px 0 10px;
  }
}
</style>
