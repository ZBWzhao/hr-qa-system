<template>
  <el-card>
    <template #header>
      <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px">
        <span style="font-weight: 600; color: #111827">知识管理</span>
        <el-button v-if="userStore.isHR || userStore.isAdmin" type="primary" @click="activeTab === 'documents' ? showAddDocument() : showAddFaq()">
          {{ activeTab === 'documents' ? '上传文档' : '新增标准答案' }}
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

      <!-- 标准答案库 -->
      <el-tab-pane label="标准答案库" name="faqs">
        <div style="display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap">
          <el-input v-model="faqKeyword" placeholder="搜索问题..." clearable style="flex: 1; min-width: 160px" @keyup.enter="fetchFaqs">
            <template #append>
              <el-button :icon="Search" @click="fetchFaqs" />
            </template>
          </el-input>
          <el-select v-model="faqCategory" placeholder="全部分类" clearable @change="fetchFaqs" style="min-width: 120px">
            <el-option label="考勤" value="attendance" />
            <el-option label="薪酬" value="salary" />
            <el-option label="福利" value="benefit" />
            <el-option label="休假" value="leave" />
            <el-option label="绩效" value="performance" />
            <el-option label="入职/其他" value="other" />
          </el-select>
        </div>
        <el-table :data="faqs" v-loading="faqLoading" stripe>
          <el-table-column prop="question" label="问题" min-width="200" show-overflow-tooltip />
          <el-table-column prop="category" label="分类" width="100">
            <template #default="{ row }"><el-tag size="small">{{ faqCategoryLabel(row.category) }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="keywords" label="关键词" min-width="150" show-overflow-tooltip>
            <template #default="{ row }">{{ row.keywords || '—' }}</template>
          </el-table-column>
          <el-table-column prop="view_count" label="浏览次数" width="100" sortable />
          <el-table-column label="操作" :width="(userStore.isHR || userStore.isAdmin) ? 220 : 80" fixed="right">
            <template #default="{ row }">
              <div style="display: flex; flex-wrap: nowrap; gap: 4px">
                <el-button size="small" @click="viewFaq(row)">查看</el-button>
                <template v-if="userStore.isHR || userStore.isAdmin">
                  <el-button size="small" type="primary" @click="showEditFaq(row)">编辑</el-button>
                  <el-button size="small" type="danger" @click="handleDeleteFaq(row)">删除</el-button>
                </template>
              </div>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination style="margin-top: 16px; justify-content: center" :current-page="faqPage" :page-size="20" :total="faqTotal" layout="prev, pager, next" @current-change="p => { faqPage = p; fetchFaqs() }" />
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

    <!-- FAQ 编辑对话框 -->
    <el-dialog v-model="faqDialogVisible" :title="faqEditId ? '编辑标准答案' : '新增标准答案'" width="min(92vw, 600px)">
      <el-form :model="faqForm" label-width="80px">
        <el-form-item label="问题"><el-input v-model="faqForm.question" /></el-form-item>
        <el-form-item label="回答"><el-input v-model="faqForm.answer" type="textarea" :rows="6" /></el-form-item>
        <el-form-item label="分类">
          <el-select v-model="faqForm.category">
            <el-option label="考勤" value="attendance" />
            <el-option label="薪酬" value="salary" />
            <el-option label="福利" value="benefit" />
            <el-option label="休假" value="leave" />
            <el-option label="绩效" value="performance" />
            <el-option label="入职/其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <div style="display: flex; gap: 8px; width: 100%">
            <el-input v-model="faqForm.keywords" placeholder="用逗号分隔" style="flex: 1" />
            <el-button type="primary" :loading="generating" @click="handleGenerateKeywords">
              <el-icon style="margin-right: 4px"><MagicStick /></el-icon>
              AI识别
            </el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="faqDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitFaq">确定</el-button>
      </template>
    </el-dialog>

    <!-- FAQ 详情抽屉 -->
    <el-drawer v-model="faqDetailVisible" title="标准答案详情" size="50%">
      <h3>{{ faqDetail.question }}</h3>
      <el-divider />
      <div style="white-space: pre-wrap; line-height: 1.8">{{ faqDetail.answer }}</div>
      <el-divider />
      <el-descriptions :column="2" border>
        <el-descriptions-item label="分类">{{ faqCategoryLabel(faqDetail.category) }}</el-descriptions-item>
        <el-descriptions-item label="浏览次数">{{ faqDetail.view_count }}</el-descriptions-item>
        <el-descriptions-item label="关键词">{{ faqDetail.keywords || '—' }}</el-descriptions-item>
      </el-descriptions>
    </el-drawer>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Document, Download, Loading, MagicStick } from '@element-plus/icons-vue'
import { getDocuments, createDocument, updateDocument, deleteDocument, publishDocument, archiveDocument, unarchiveDocument, getDocument, classifyDocument } from '../api/documents'
import { getFaqs, getAllFaqs, getFaq, createFaq, updateFaq, deleteFaq, generateKeywords } from '../api/faqs'
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

// FAQ 相关
const faqLoading = ref(false)
const faqs = ref([])
const faqPage = ref(1)
const faqTotal = ref(0)
const faqKeyword = ref('')
const faqCategory = ref('')
const faqDialogVisible = ref(false)
const faqEditId = ref(null)
const faqForm = reactive({ question: '', answer: '', category: 'other', keywords: '' })
const faqDetailVisible = ref(false)
const faqDetail = ref({})
const generating = ref(false)

// 文档相关函数
function categoryLabel(c) { return { attendance: '考勤', salary: '薪酬', benefit: '福利', leave: '休假', performance: '绩效', other: '其他' }[c] || c }
function statusType(s) { return { draft: 'info', published: 'success', archived: 'warning' }[s] || '' }
function statusLabel(s) { return { draft: '草稿', published: '已发布', archived: '已归档' }[s] || s }

function highlightTitle(title, keyword) {
  if (!keyword || !title) return title
  const regex = new RegExp(`(${keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
  return title.replace(regex, '<em style="color: #f5222d; font-style: normal; font-weight: 600">$1</em>')
}

function downloadFile(doc) {
  if (!doc.file_path) { ElMessage.warning('该文档没有附件'); return }
  const link = document.createElement('a')
  link.href = `/api/v1/documents/${doc.id}/download`
  link.download = doc.file_path.split('/').pop()?.split('\\').pop() || '附件'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
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

// FAQ 相关函数
function faqCategoryLabel(c) { return { attendance: '考勤', salary: '薪酬', benefit: '福利', leave: '休假', performance: '绩效', other: '入职/其他' }[c] || c || '—' }

async function fetchFaqs() {
  faqLoading.value = true
  try {
    const api = (userStore.isHR || userStore.isAdmin) ? getAllFaqs : getFaqs
    const res = await api({ page: faqPage.value, keyword: faqKeyword.value, category: faqCategory.value })
    faqs.value = res.data?.items || []
    faqTotal.value = res.data?.total || 0
  } catch (e) {} finally { faqLoading.value = false }
}

function showAddFaq() {
  faqEditId.value = null
  Object.assign(faqForm, { question: '', answer: '', category: 'other', keywords: '' })
  faqDialogVisible.value = true
}

function showEditFaq(row) {
  faqEditId.value = row.id
  Object.assign(faqForm, { question: row.question, answer: row.answer, category: row.category || 'other', keywords: row.keywords || '' })
  faqDialogVisible.value = true
}

async function viewFaq(row) {
  const res = await getFaq(row.id)
  faqDetail.value = res.data
  faqDetailVisible.value = true
  row.view_count = res.data.view_count
}

async function submitFaq() {
  if (faqEditId.value) { await updateFaq(faqEditId.value, faqForm) }
  else { await createFaq(faqForm) }
  ElMessage.success('操作成功')
  faqDialogVisible.value = false
  fetchFaqs()
}

async function handleDeleteFaq(row) { await ElMessageBox.confirm('确认删除？', '提示', { type: 'warning' }); await deleteFaq(row.id); ElMessage.success('删除成功'); fetchFaqs() }

async function handleGenerateKeywords() {
  if (!faqForm.question && !faqForm.answer) { ElMessage.warning('请先输入问题或回答'); return }
  generating.value = true
  try {
    const res = await generateKeywords({ question: faqForm.question, answer: faqForm.answer })
    if (res.data?.keywords) { faqForm.keywords = res.data.keywords; ElMessage.success('关键词生成成功') }
  } catch (e) { ElMessage.error('关键词生成失败') } finally { generating.value = false }
}

watch(activeTab, (tab) => {
  if (tab === 'documents') fetchDocuments()
  else if (tab === 'faqs') fetchFaqs()
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
