<template>
  <el-card>
    <template #header>
      <div style="display: flex; justify-content: space-between; align-items: center">
        <span style="font-weight: 600; color: #111827">制度文档管理</span>
        <el-button type="primary" @click="showDialog()">上传文档</el-button>
      </div>
    </template>
    <div style="display: flex; gap: 12px; margin-bottom: 16px">
      <el-select v-model="filters.category" placeholder="全部分类" clearable @change="fetchData">
        <el-option label="考勤" value="attendance" />
        <el-option label="薪酬" value="salary" />
        <el-option label="福利" value="benefit" />
        <el-option label="休假" value="leave" />
        <el-option label="绩效" value="performance" />
        <el-option label="其他" value="other" />
      </el-select>
      <el-select v-model="filters.status" placeholder="全部状态" clearable @change="fetchData">
        <el-option label="草稿" value="draft" />
        <el-option label="已发布" value="published" />
        <el-option label="已归档" value="archived" />
      </el-select>
    </div>
    <el-table :data="documents" v-loading="loading" stripe>
      <el-table-column prop="title" label="文档标题" min-width="200" />
      <el-table-column prop="category" label="分类" width="100">
        <template #default="{ row }">
          <el-tag size="small">{{ categoryLabel(row.category) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="version" label="版本" width="80" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="120">
        <template #default="{ row }">{{ row.created_at?.substring(0, 10) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="viewDetail(row)">详情</el-button>
          <el-button v-if="row.status === 'draft'" size="small" type="success" @click="handlePublish(row)">发布</el-button>
          <el-button v-if="row.status === 'published'" size="small" type="warning" @click="handleArchive(row)">归档</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination style="margin-top: 16px; justify-content: center" :current-page="page" :page-size="20" :total="total" layout="prev, pager, next" @current-change="p => { page = p; fetchData() }" />

    <el-dialog v-model="dialogVisible" :title="editId ? '编辑文档' : '上传文档'" width="600px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.category">
            <el-option label="考勤" value="attendance" />
            <el-option label="薪酬" value="salary" />
            <el-option label="福利" value="benefit" />
            <el-option label="休假" value="leave" />
            <el-option label="绩效" value="performance" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="内容"><el-input v-model="form.content_text" type="textarea" :rows="10" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="detailVisible" title="文档详情" size="60%">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="标题">{{ detail.title }}</el-descriptions-item>
        <el-descriptions-item label="分类">{{ categoryLabel(detail.category) }}</el-descriptions-item>
        <el-descriptions-item label="版本">{{ detail.version }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ statusLabel(detail.status) }}</el-descriptions-item>
      </el-descriptions>
      <el-divider />
      <div style="white-space: pre-wrap; line-height: 1.8">{{ detail.content_text }}</div>
    </el-drawer>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getDocuments, createDocument, updateDocument, deleteDocument, publishDocument, archiveDocument, getDocument } from '../api/documents'

const route = useRoute()
const loading = ref(false)
const documents = ref([])
const page = ref(1)
const total = ref(0)
const filters = reactive({ category: '', status: '' })
const dialogVisible = ref(false)
const editId = ref(null)
const form = reactive({ title: '', category: 'other', content_text: '' })
const detailVisible = ref(false)
const detail = ref({})

function categoryLabel(c) {
  return { attendance: '考勤', salary: '薪酬', benefit: '福利', leave: '休假', performance: '绩效', other: '其他' }[c] || c
}
function statusType(s) {
  return { draft: 'info', published: 'success', archived: 'warning' }[s] || ''
}
function statusLabel(s) {
  return { draft: '草稿', published: '已发布', archived: '已归档' }[s] || s
}

async function fetchData() {
  loading.value = true
  try {
    const res = await getDocuments({ page: page.value, ...filters })
    documents.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch (e) {} finally { loading.value = false }
}

function showDialog() {
  editId.value = null
  Object.assign(form, { title: '', category: 'other', content_text: '' })
  dialogVisible.value = true
}

async function handleSubmit() {
  try {
    if (editId.value) {
      await updateDocument(editId.value, form)
    } else {
      const fd = new FormData()
      fd.append('title', form.title)
      fd.append('category', form.category)
      fd.append('content_text', form.content_text)
      await createDocument(fd)
    }
    ElMessage.success('操作成功')
    dialogVisible.value = false
    fetchData()
  } catch (e) {}
}

async function viewDetail(row) {
  try {
    const res = await getDocument(row.id)
    detail.value = res.data
    detailVisible.value = true
  } catch (e) {}
}

async function handlePublish(row) {
  await ElMessageBox.confirm('确认发布该文档？', '提示')
  await publishDocument(row.id)
  ElMessage.success('发布成功')
  fetchData()
}

async function handleArchive(row) {
  await ElMessageBox.confirm('确认归档该文档？', '提示')
  await archiveDocument(row.id)
  ElMessage.success('归档成功')
  fetchData()
}

async function handleDelete(row) {
  await ElMessageBox.confirm('确认删除该文档？', '提示', { type: 'warning' })
  await deleteDocument(row.id)
  ElMessage.success('删除成功')
  fetchData()
}

onMounted(() => {
  fetchData()
  if (route.query.id) viewDetail({ id: route.query.id })
})
</script>