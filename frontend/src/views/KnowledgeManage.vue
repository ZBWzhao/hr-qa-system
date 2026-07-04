<template>
  <el-card>
    <template #header>
      <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px">
        <span style="font-weight: 600; color: #111827">知识管理</span>
        <el-button v-if="userStore.isHR || userStore.isAdmin" type="primary" @click="showAddDocument()">
          上传文档
        </el-button>
      </div>
    </template>

    <el-tabs v-model="activeTab">
      <!-- 制度文档 -->
      <el-tab-pane label="制度文档" name="documents">
        <div style="display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap">
          <el-input v-model="docFilters.keyword" placeholder="搜索标题或内容..." clearable style="flex: 1; min-width: 160px" @keyup.enter="fetchDocuments" @clear="fetchDocuments">
            <template #append>
              <el-button :icon="Search" @click="fetchDocuments" />
            </template>
          </el-input>
          <el-select v-model="docFilters.category" placeholder="全部分类" clearable @change="fetchDocuments" style="min-width: 120px">
            <el-option label="考勤" value="attendance" />
            <el-option label="薪酬" value="salary" />
            <el-option label="福利" value="benefit" />
            <el-option label="休假" value="leave" />
            <el-option label="绩效" value="performance" />
            <el-option label="其他" value="other" />
          </el-select>
          <el-select v-if="userStore.isHR || userStore.isAdmin" v-model="docFilters.status" placeholder="全部状态" clearable @change="fetchDocuments" style="min-width: 120px">
            <el-option label="草稿" value="draft" />
            <el-option label="已发布" value="published" />
            <el-option label="已归档" value="archived" />
          </el-select>
        </div>
        <el-table :data="documents" v-loading="docLoading" stripe>
          <el-table-column prop="title" label="文档标题" min-width="250">
            <template #default="{ row }">
              <div>
                <span v-html="highlightTitle(row.title, docFilters.keyword)"></span>
              </div>
              <div v-if="row.highlighted_content" class="search-snippet" v-html="row.highlighted_content"></div>
            </template>
          </el-table-column>
          <el-table-column prop="category" label="分类" width="100">
            <template #default="{ row }"><el-tag size="small">{{ categoryLabel(row.category) }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="uploader_name" label="上传人" width="100" />
          <el-table-column prop="version" label="版本" width="80" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }"><el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="120">
            <template #default="{ row }">{{ row.created_at?.substring(0, 10) }}</template>
          </el-table-column>
          <el-table-column label="操作" :width="(userStore.isHR || userStore.isAdmin) ? 300 : 80" fixed="right">
            <template #default="{ row }">
              <div style="display: flex; flex-wrap: nowrap; gap: 4px">
                <el-button size="small" @click="viewDocDetail(row)">详情</el-button>
                <template v-if="userStore.isHR || userStore.isAdmin">
                  <el-button size="small" type="primary" @click="showEditDoc(row)">编辑</el-button>
                  <el-button v-if="row.status === 'draft'" size="small" type="success" @click="handlePublish(row)">发布</el-button>
                  <el-button v-if="row.status === 'published'" size="small" type="warning" @click="handleArchive(row)">归档</el-button>
                  <el-button v-if="row.status === 'archived'" size="small" type="success" @click="handleUnarchive(row)">下架</el-button>
                  <el-button size="small" type="danger" @click="handleDeleteDoc(row)">删除</el-button>
                </template>
              </div>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination style="margin-top: 16px; justify-content: center" :current-page="docPage" :page-size="20" :total="docTotal" layout="prev, pager, next" @current-change="p => { docPage = p; fetchDocuments() }" />
      </el-tab-pane>
    </el-tabs>

    <!-- 文档详情抽屉 -->
    <el-drawer v-model="docDetailVisible" title="文档详情" :size="isMobile ? '88vw' : '60%'">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="标题">{{ docDetail.title }}</el-descriptions-item>
        <el-descriptions-item label="分类">{{ categoryLabel(docDetail.category) }}</el-descriptions-item>
        <el-descriptions-item label="版本">{{ docDetail.version }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ statusLabel(docDetail.status) }}</el-descriptions-item>
        <el-descriptions-item label="上传人">{{ docDetail.uploader_name || '—' }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ docDetail.updated_at?.substring(0, 19) }}</el-descriptions-item>
      </el-descriptions>
      <div v-if="docDetail.file_path" style="margin-top: 16px">
        <h4>附件</h4>
        <div class="attachment-item">
          <el-icon style="margin-right: 8px; color: #D97706"><Document /></el-icon>
          <span>{{ docDetail.file_path?.split('/').pop()?.split('\\').pop() || '附件' }}</span>
          <el-tag size="small" style="margin-left: 8px" type="info">{{ docDetail.file_type || '未知' }}</el-tag>
          <el-button size="small" type="primary" style="margin-left: auto" @click="downloadFile(docDetail)">
            <el-icon style="margin-right: 4px"><Download /></el-icon>
            下载
          </el-button>
        </div>
      </div>
      <el-divider />
      <h4>正文内容</h4>
      <div style="white-space: pre-wrap; line-height: 1.8; max-height: 400px; overflow-y: auto">{{ docDetail.content_text }}</div>
      <el-divider />
      <h4>版本历史</h4>
      <el-table :data="docDetail.versions || []" size="small" stripe>
        <el-table-column prop="version" label="版本" width="80" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
      </el-table>
    </el-drawer>

    <!-- 文档编辑对话框 -->
    <el-dialog v-model="docDialogVisible" :title="docEditId ? '编辑文档' : '上传文档'" width="min(92vw, 700px)">
      <el-form :model="docForm" label-width="80px">
        <el-form-item label="标题"><el-input v-model="docForm.title" placeholder="留空则使用文件名" /></el-form-item>
        <el-form-item label="分类">
          <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap">
            <el-select v-model="docForm.category" style="width: 200px">
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
          <el-upload ref="uploadRef" :auto-upload="false" :limit="1" :on-change="handleFileChange" :on-remove="handleFileRemove" accept=".txt,.md,.docx,.pdf">
            <el-button type="primary" size="small">选择文件</el-button>
            <template #tip>
              <div style="color: #9CA3AF; font-size: 12px; margin-top: 4px">支持 txt、md、docx、pdf 格式</div>
            </template>
          </el-upload>
        </el-form-item>
        <el-form-item label="手动录入">
          <el-input v-model="docForm.content_text" type="textarea" :rows="8" placeholder="可在此手动输入文档内容" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="docDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitDoc">确定</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Document, Download, Loading } from '@element-plus/icons-vue'
import { getDocuments, createDocument, updateDocument, deleteDocument, publishDocument, archiveDocument, unarchiveDocument, getDocument, classifyDocument, downloadDocument } from '../api/documents'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const activeTab = ref('documents')
const isMobile = ref(window.innerWidth <= 768)
function handleResize() { isMobile.value = window.innerWidth <= 768 }

// 文档相关
const docLoading = ref(false)
const documents = ref([])
const docPage = ref(1)
const docTotal = ref(0)
const docFilters = reactive({ keyword: '', category: '', status: '' })
const docDialogVisible = ref(false)
const docEditId = ref(null)
const docForm = reactive({ title: '', category: 'other', content_text: '' })
const selectedFile = ref(null)
const docDetailVisible = ref(false)
const docDetail = ref({})
const classifying = ref(false)
const categoryConfidence = ref(null)

// 文档相关函数
function categoryLabel(c) { return { attendance: '考勤', salary: '薪酬', benefit: '福利', leave: '休假', performance: '绩效', other: '其他' }[c] || c }
function statusType(s) { return { draft: 'info', published: 'success', archived: 'warning' }[s] || '' }
function statusLabel(s) { return { draft: '草稿', published: '已发布', archived: '已归档' }[s] || s }

function highlightTitle(title, keyword) {
  if (!keyword || !title) return title
  const regex = new RegExp(`(${keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
  return title.replace(regex, '<em style="color: #f5222d; font-style: normal; font-weight: 600">$1</em>')
}

async function downloadFile(doc) {
  if (!doc.file_path) { ElMessage.warning('该文档没有附件'); return }
  const fileName = doc.file_path.split('/').pop()?.split('\\').pop() || '附件'
  try {
    const blob = await downloadDocument(doc.id)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = fileName
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (e) {
    ElMessage.error('下载失败，请稍后重试')
  }
}

async function fetchDocuments() {
  docLoading.value = true
  try {
    const params = { page: docPage.value, ...docFilters }
    if (!userStore.isHR && !userStore.isAdmin) delete params.status
    const res = await getDocuments(params)
    documents.value = res.data?.items || []
    docTotal.value = res.data?.total || 0
  } catch (e) {} finally { docLoading.value = false }
}

function showAddDocument() {
  docEditId.value = null
  selectedFile.value = null
  categoryConfidence.value = null
  Object.assign(docForm, { title: '', category: 'other', content_text: '' })
  docDialogVisible.value = true
}

async function showEditDoc(row) {
  const res = await getDocument(row.id)
  const doc = res.data
  docEditId.value = doc.id
  selectedFile.value = null
  Object.assign(docForm, { title: doc.title, category: doc.category, content_text: doc.content_text || '' })
  docDialogVisible.value = true
}

function handleFileChange(file) {
  selectedFile.value = file.raw
  if (!docForm.title) docForm.title = file.name.replace(/\.[^.]+$/, '')
  autoClassify(file.raw)
}

function handleFileRemove() { selectedFile.value = null; categoryConfidence.value = null }

async function autoClassify(file) {
  classifying.value = true
  categoryConfidence.value = null
  try {
    const fd = new FormData()
    fd.append('file', file)
    const res = await classifyDocument(fd)
    if (res.data?.category) {
      docForm.category = res.data.category
      categoryConfidence.value = res.data.confidence || 0
    }
    if (res.data?.content_text && !docForm.content_text) {
      docForm.content_text = res.data.content_text
    }
    if (res.data?.suggested_title && !docForm.title) {
      docForm.title = res.data.suggested_title
    }
  } catch (e) {} finally { classifying.value = false }
}

async function submitDoc() {
  const fd = new FormData()
  fd.append('title', docForm.title)
  fd.append('category', docForm.category)
  if (docForm.content_text) fd.append('content_text', docForm.content_text)
  if (selectedFile.value) fd.append('file', selectedFile.value)
  if (docEditId.value) { await updateDocument(docEditId.value, fd) }
  else { await createDocument(fd) }
  ElMessage.success('操作成功')
  docDialogVisible.value = false
  fetchDocuments()
}

async function viewDocDetail(row) {
  const res = await getDocument(row.id)
  docDetail.value = res.data
  docDetailVisible.value = true
}

async function handlePublish(row) { await ElMessageBox.confirm('确认发布？', '提示'); await publishDocument(row.id); ElMessage.success('发布成功'); fetchDocuments() }
async function handleArchive(row) { await ElMessageBox.confirm('确认归档？', '提示'); await archiveDocument(row.id); ElMessage.success('归档成功'); fetchDocuments() }
async function handleUnarchive(row) { await ElMessageBox.confirm('确认下架？', '提示'); await unarchiveDocument(row.id); ElMessage.success('下架成功'); fetchDocuments() }
async function handleDeleteDoc(row) { await ElMessageBox.confirm('确认删除？', '提示', { type: 'warning' }); await deleteDocument(row.id); ElMessage.success('删除成功'); fetchDocuments() }

watch(activeTab, (tab) => {
  if (tab === 'documents') fetchDocuments()
})

onMounted(() => {
  fetchDocuments()
  window.addEventListener('resize', handleResize)
})
onBeforeUnmount(() => window.removeEventListener('resize', handleResize))
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
