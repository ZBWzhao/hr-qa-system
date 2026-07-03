<template>
  <el-card>
    <template #header>
      <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px">
        <span style="font-weight: 600; color: #111827">制度文档管理</span>
        <el-button v-if="userStore.isHR || userStore.isAdmin" type="primary" @click="showDialog()">上传文档</el-button>
      </div>
    </template>
    <div style="display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap">
      <el-input v-model="filters.keyword" placeholder="搜索标题或内容..." clearable style="flex: 1; min-width: 160px" @keyup.enter="fetchData" @clear="fetchData">
        <template #append>
          <el-button :icon="Search" @click="fetchData" />
        </template>
      </el-input>
      <el-select v-model="filters.category" placeholder="全部分类" clearable @change="fetchData">
        <el-option label="考勤" value="attendance" />
        <el-option label="薪酬" value="salary" />
        <el-option label="福利" value="benefit" />
        <el-option label="休假" value="leave" />
        <el-option label="绩效" value="performance" />
        <el-option label="其他" value="other" />
      </el-select>
      <el-select v-if="userStore.isHR || userStore.isAdmin" v-model="filters.status" placeholder="全部状态" clearable @change="fetchData">
        <el-option label="草稿" value="draft" />
        <el-option label="已发布" value="published" />
        <el-option label="已归档" value="archived" />
      </el-select>
    </div>
    <el-table :data="documents" v-loading="loading" stripe>
      <el-table-column prop="title" label="文档标题" min-width="250">
        <template #default="{ row }">
          <div>
            <span v-html="highlightTitle(row.title)"></span>
          </div>
          <div v-if="row.highlighted_content" class="search-snippet" v-html="row.highlighted_content"></div>
        </template>
      </el-table-column>
      <el-table-column prop="category" label="分类" width="100">
        <template #default="{ row }">
          <el-tag size="small">{{ categoryLabel(row.category) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="uploader_name" label="上传人" width="100" />
      <el-table-column prop="version" label="版本" width="80" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="120">
        <template #default="{ row }">{{ row.created_at?.substring(0, 10) }}</template>
      </el-table-column>
      <el-table-column label="操作" :width="(userStore.isHR || userStore.isAdmin) ? 300 : 80" fixed="right">
        <template #default="{ row }">
          <div style="display: flex; flex-wrap: nowrap; gap: 4px">
            <el-button size="small" @click="viewDetail(row)">详情</el-button>
            <template v-if="userStore.isHR || userStore.isAdmin">
              <el-button size="small" type="primary" @click="showEdit(row)">编辑</el-button>
              <el-button v-if="row.status === 'draft'" size="small" type="success" @click="handlePublish(row)">发布</el-button>
              <el-button v-if="row.status === 'published'" size="small" type="warning" @click="handleArchive(row)">归档</el-button>
              <el-button v-if="row.status === 'archived'" size="small" type="success" @click="handleUnarchive(row)">下架</el-button>
              <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
            </template>
          </div>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination style="margin-top: 16px; justify-content: center" :current-page="page" :page-size="20" :total="total" layout="prev, pager, next" @current-change="p => { page = p; fetchData() }" />

    <!-- 新增文档弹窗：文件上传 + 手动录入同时可用 -->
    <el-dialog v-model="dialogVisible" :title="editId ? '编辑文档' : '新增文档'" width="700px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题"><el-input v-model="form.title" placeholder="留空则使用文件名" /></el-form-item>
        <el-form-item label="分类">
          <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap">
            <el-select v-model="form.category" style="width: 200px">
              <el-option label="考勤" value="attendance" />
              <el-option label="薪酬" value="salary" />
              <el-option label="福利" value="benefit" />
              <el-option label="休假" value="leave" />
              <el-option label="绩效" value="performance" />
              <el-option label="其他" value="other" />
            </el-select>
            <template v-if="classifying">
              <el-icon class="is-loading" style="color: #D97706"><Loading /></el-icon>
              <span style="color: #9CA3AF; font-size: 13px">正在分析文档分类...</span>
            </template>
            <template v-else-if="categoryConfidence">
              <el-tag type="success" size="small">置信度: {{ categoryConfidence }}%</el-tag>
            </template>
          </div>
        </el-form-item>
        <el-form-item label="上传文件">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            :on-exceed="() => ElMessage.warning('只能上传一个文件')"
            accept=".txt,.md,.docx,.pdf"
          >
            <el-button type="primary" size="small">选择文件</el-button>
            <template #tip>
              <div style="color: #9CA3AF; font-size: 12px; margin-top: 4px">支持 txt、md、docx、pdf 格式（可选，与手动录入内容合并）</div>
            </template>
          </el-upload>
        </el-form-item>
        <el-form-item label="手动录入">
          <el-input v-model="form.content_text" type="textarea" :rows="8" placeholder="可在此手动输入文档内容，与上传文件内容合并保存" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 文档详情抽屉 -->
    <el-drawer v-model="detailVisible" title="文档详情" size="60%">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="标题">{{ detail.title }}</el-descriptions-item>
        <el-descriptions-item label="分类">{{ categoryLabel(detail.category) }}</el-descriptions-item>
        <el-descriptions-item label="版本">{{ detail.version }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ statusLabel(detail.status) }}</el-descriptions-item>
        <el-descriptions-item label="上传人">{{ detail.uploader_name || '—' }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ detail.updated_at?.substring(0, 19) }}</el-descriptions-item>
      </el-descriptions>

      <!-- 附件信息 -->
      <div v-if="detail.file_path" style="margin-top: 16px">
        <h4>附件</h4>
        <div class="attachment-item">
          <el-icon style="margin-right: 8px; color: #D97706"><Document /></el-icon>
          <span>{{ detail.file_path?.split('/').pop()?.split('\\').pop() || '附件' }}</span>
          <el-tag size="small" style="margin-left: 8px" type="info">{{ detail.file_type || '未知' }}</el-tag>
          <el-button size="small" type="primary" style="margin-left: auto" @click="downloadFile(detail)">
            <el-icon style="margin-right: 4px"><Download /></el-icon>
            下载
          </el-button>
        </div>
      </div>

      <el-divider />
      <h4>正文内容</h4>
      <div style="white-space: pre-wrap; line-height: 1.8; max-height: 400px; overflow-y: auto">{{ detail.content_text }}</div>
      <el-divider />
      <h4>版本历史</h4>
      <el-table :data="detail.versions || []" size="small" stripe>
        <el-table-column prop="version" label="版本" width="80" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
      </el-table>
    </el-drawer>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, Search, Loading, Download } from '@element-plus/icons-vue'
import { getDocuments, createDocument, updateDocument, deleteDocument, publishDocument, archiveDocument, getDocument, classifyDocument } from '../api/documents'
import { useUserStore } from '../stores/user'

const route = useRoute()
const userStore = useUserStore()
const loading = ref(false)
const documents = ref([])
const page = ref(1)
const total = ref(0)
const filters = reactive({ keyword: '', category: '', status: '' })
const dialogVisible = ref(false)
const editId = ref(null)
const form = reactive({ title: '', category: 'other', content_text: '' })
const selectedFile = ref(null)
const detailVisible = ref(false)
const detail = ref({})
const classifying = ref(false)
const categoryConfidence = ref(null)

// 搜索高亮
function highlightTitle(title) {
  const kw = filters.keyword?.trim()
  if (!kw || !title) return title
  const regex = new RegExp(`(${kw.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
  return title.replace(regex, '<em style="color: #f5222d; font-style: normal; font-weight: 600">$1</em>')
}

// 下载附件
function downloadFile(doc) {
  if (!doc.file_path) {
    ElMessage.warning('该文档没有附件')
    return
  }
  // 构建下载链接
  const fileName = doc.file_path.split('/').pop()?.split('\\').pop() || '附件'
  const downloadUrl = `/api/v1/documents/${doc.id}/download`

  // 创建临时链接触发下载
  const link = document.createElement('a')
  link.href = downloadUrl
  link.download = fileName
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

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
    const params = { page: page.value, ...filters }
    if (!userStore.isHR) delete params.status
    const res = await getDocuments(params)
    documents.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch (e) {} finally { loading.value = false }
}

function showDialog() {
  editId.value = null
  selectedFile.value = null
  categoryConfidence.value = null
  Object.assign(form, { title: '', category: 'other', content_text: '' })
  dialogVisible.value = true
}

async function showEdit(row) {
  try {
    const res = await getDocument(row.id)
    const doc = res.data
    editId.value = doc.id
    selectedFile.value = null
    Object.assign(form, { title: doc.title, category: doc.category, content_text: doc.content_text || '' })
    dialogVisible.value = true
  } catch (e) {}
}

function handleFileChange(file) {
  const ext = file.name.split('.').pop().toLowerCase()
  if (['exe', 'zip', 'bat', 'cmd', 'sh', 'msi'].includes(ext)) {
    ElMessage.error(`不支持上传 ${ext} 格式文件`)
    return false
  }
  if (['xlsx', 'xls'].includes(ext)) {
    ElMessage.warning('暂不支持解析该格式，请使用 txt/md/docx/pdf 或手动录入')
    return false
  }
  if (file.size === 0) {
    ElMessage.warning('文件内容为空')
    return false
  }
  selectedFile.value = file.raw
  if (!form.title) {
    form.title = file.name.replace(/\.[^.]+$/, '')
  }
  // 触发自动分类
  autoClassify(file.raw)
}

function handleFileRemove() {
  selectedFile.value = null
  categoryConfidence.value = null
}

async function autoClassify(file) {
  classifying.value = true
  categoryConfidence.value = null
  try {
    const fd = new FormData()
    fd.append('file', file)
    const res = await classifyDocument(fd)
    if (res.data?.category) {
      form.category = res.data.category
      categoryConfidence.value = res.data.confidence || 0
    }
  } catch (e) {
    // 分类失败不影响上传
  } finally {
    classifying.value = false
  }
}

async function handleSubmit() {
  try {
    const fd = new FormData()
    fd.append('title', form.title)
    fd.append('category', form.category)
    if (form.content_text) fd.append('content_text', form.content_text)
    if (selectedFile.value) fd.append('file', selectedFile.value)
    if (editId.value) {
      await updateDocument(editId.value, fd)
    } else {
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

async function handleUnarchive(row) {
  await ElMessageBox.confirm('确认下架该文档？下架后将变为草稿状态。', '提示')
  await unarchiveDocument(row.id)
  ElMessage.success('下架成功')
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

<style scoped>
.attachment-item {
  display: flex;
  align-items: center;
  padding: 10px 14px;
  background: #f9fafb;
  border: 1px solid #f3f4f6;
  border-radius: 8px;
  color: #374151;
  font-size: 14px;
}
.search-snippet {
  font-size: 12px;
  color: #6B7280;
  margin-top: 6px;
  line-height: 1.6;
  max-height: 60px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}
.search-snippet :deep(em) {
  color: #f5222d;
  font-style: normal;
  font-weight: 600;
  background: #fff1f0;
  padding: 0 2px;
  border-radius: 2px;
}
</style>
