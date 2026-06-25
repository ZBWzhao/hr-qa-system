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
        <el-option label="休假" value="leave" />
        <el-option label="绩效" value="performance" />
        <el-option label="入职" value="other" />
      </el-select>
    </div>
    <el-table :data="faqs" v-loading="loading" stripe>
      <el-table-column prop="question" label="问题" min-width="250" />
      <el-table-column prop="category" label="分类" width="100">
        <template #default="{ row }"><el-tag size="small">{{ row.category || '—' }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="view_count" label="浏览次数" width="100" sortable />
      <el-table-column label="操作" :width="userStore.isHR ? 180 : 80">
        <template #default="{ row }">
          <el-button size="small" @click="viewFaq(row)">查看</el-button>
          <template v-if="userStore.isHR">
            <el-button size="small" type="primary" @click="showDialog(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
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
            <el-option label="休假" value="leave" />
            <el-option label="绩效" value="performance" />
            <el-option label="入职" value="other" />
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
      <div style="margin-top: 16px; color: #9CA3AF">浏览次数：{{ detail.view_count }}</div>
    </el-drawer>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getFaqs, getAllFaqs, createFaq, updateFaq, deleteFaq } from '../api/faqs'
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
    Object.assign(form, row)
  } else {
    Object.assign(form, { question: '', answer: '', category: 'other', keywords: '' })
  }
  dialogVisible.value = true
}

function viewFaq(row) {
  detail.value = row
  detailVisible.value = true
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