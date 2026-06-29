<template>
  <el-card>
    <template #header>
      <div style="display: flex; justify-content: space-between; align-items: center">
        <span style="font-weight: 600; color: #111827">FAQ 管理</span>
        <el-button v-if="userStore.isHR" type="primary" @click="showDialog()">新增FAQ</el-button>
      </div>
    </template>
    <div style="display: flex; gap: 12px; margin-bottom: 16px">
      <el-input v-model="keyword" placeholder="搜索问题..." clearable style="width: 300px" @keyup.enter="fetchData" />
      <el-select v-model="category" placeholder="全部分类" clearable @change="fetchData">
        <el-option label="考勤" value="attendance" />
        <el-option label="薪酬" value="salary" />
        <el-option label="福利" value="benefit" />
        <el-option label="休假" value="leave" />
        <el-option label="绩效" value="performance" />
        <el-option label="入职/其他" value="other" />
      </el-select>
    </div>
    <el-table :data="faqs" v-loading="loading" stripe>
      <el-table-column prop="question" label="问题" min-width="200" show-overflow-tooltip />
      <el-table-column prop="category" label="分类" width="100">
        <template #default="{ row }"><el-tag size="small">{{ categoryLabel(row.category) }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="keywords" label="关键词" min-width="150" show-overflow-tooltip>
        <template #default="{ row }">{{ row.keywords || '—' }}</template>
      </el-table-column>
      <el-table-column prop="view_count" label="浏览次数" width="100" sortable />
      <el-table-column label="操作" :width="userStore.isHR ? 220 : 80" fixed="right">
        <template #default="{ row }">
          <div style="display: flex; flex-wrap: nowrap; gap: 4px">
            <el-button size="small" @click="viewFaq(row)">查看</el-button>
            <template v-if="userStore.isHR">
              <el-button size="small" type="primary" @click="showDialog(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
            </template>
          </div>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination style="margin-top: 16px; justify-content: center" :current-page="page" :page-size="20" :total="total" layout="prev, pager, next" @current-change="p => { page = p; fetchData() }" />

    <el-dialog v-model="dialogVisible" :title="editId ? '编辑FAQ' : '新增FAQ'" width="600px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="问题"><el-input v-model="form.question" /></el-form-item>
        <el-form-item label="回答"><el-input v-model="form.answer" type="textarea" :rows="6" /></el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.category">
            <el-option label="考勤" value="attendance" />
            <el-option label="薪酬" value="salary" />
            <el-option label="福利" value="benefit" />
            <el-option label="休假" value="leave" />
            <el-option label="绩效" value="performance" />
            <el-option label="入职/其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词"><el-input v-model="form.keywords" placeholder="用逗号分隔" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="detailVisible" title="FAQ详情" size="50%">
      <h3>{{ detail.question }}</h3>
      <el-divider />
      <div style="white-space: pre-wrap; line-height: 1.8">{{ detail.answer }}</div>
      <el-divider />
      <el-descriptions :column="2" border>
        <el-descriptions-item label="分类">{{ categoryLabel(detail.category) }}</el-descriptions-item>
        <el-descriptions-item label="浏览次数">{{ detail.view_count }}</el-descriptions-item>
        <el-descriptions-item label="关键词">{{ detail.keywords || '—' }}</el-descriptions-item>
      </el-descriptions>
    </el-drawer>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getFaqs, getAllFaqs, getFaq, createFaq, updateFaq, deleteFaq } from '../api/faqs'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const loading = ref(false)
const faqs = ref([])
const page = ref(1)
const total = ref(0)
const keyword = ref('')
const category = ref('')
const dialogVisible = ref(false)
const editId = ref(null)
const form = reactive({ question: '', answer: '', category: 'other', keywords: '' })
const detailVisible = ref(false)
const detail = ref({})

function categoryLabel(c) {
  return { attendance: '考勤', salary: '薪酬', benefit: '福利', leave: '休假', performance: '绩效', other: '入职/其他' }[c] || c || '—'
}

async function fetchData() {
  loading.value = true
  try {
    const api = userStore.isHR ? getAllFaqs : getFaqs
    const res = await api({ page: page.value, keyword: keyword.value, category: category.value })
    faqs.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch (e) {} finally { loading.value = false }
}

function showDialog(row) {
  editId.value = row?.id || null
  if (row) {
    Object.assign(form, { question: row.question, answer: row.answer, category: row.category || 'other', keywords: row.keywords || '' })
  } else {
    Object.assign(form, { question: '', answer: '', category: 'other', keywords: '' })
  }
  dialogVisible.value = true
}

async function viewFaq(row) {
  try {
    const res = await getFaq(row.id)
    detail.value = res.data
    detailVisible.value = true
    // 更新列表中的浏览次数
    row.view_count = res.data.view_count
  } catch (e) {}
}

async function handleSubmit() {
  try {
    if (editId.value) {
      await updateFaq(editId.value, form)
    } else {
      await createFaq(form)
    }
    ElMessage.success('操作成功')
    dialogVisible.value = false
    fetchData()
  } catch (e) {}
}

async function handleDelete(row) {
  await ElMessageBox.confirm('确认删除？', '提示', { type: 'warning' })
  await deleteFaq(row.id)
  ElMessage.success('删除成功')
  fetchData()
}

onMounted(() => fetchData())
</script>
