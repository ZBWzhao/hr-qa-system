<template>
  <div class="guide-page">
    <div class="guide-header">
      <el-button text @click="$router.push('/chat')">
        <el-icon><ArrowLeft /></el-icon> 返回智能问答
      </el-button>
      <div class="header-title">
        <h2>新员工速查指引</h2>
        <p class="guide-sub">常见办公、请假、人事问题快速查阅（独立于智能问答，不会写入对话记录）</p>
      </div>
      <el-button v-if="isHR" type="primary" @click="openManageDialog">
        <el-icon><Edit /></el-icon> 管理指引
      </el-button>
    </div>

    <el-row :gutter="20">
      <el-col :xs="24" :md="10">
        <div class="left-card-wrapper">
          <el-card shadow="never" class="left-card">
            <el-collapse v-model="activeCategories">
              <el-collapse-item v-for="cat in categories" :key="cat.id" :title="cat.title" :name="cat.id">
                <div
                  v-for="item in cat.items"
                  :key="item.id"
                  :class="['guide-item', { active: selectedId === item.id }]"
                  @click="selectItem(item.id)"
                >
                  {{ item.question }}
                </div>
              </el-collapse-item>
            </el-collapse>
          </el-card>
        </div>
      </el-col>
      <el-col :xs="24" :md="14">
        <div class="answer-card-wrapper">
          <el-card shadow="never" class="answer-card">
            <template v-if="selectedItem">
              <el-tag size="small" type="warning" style="margin-bottom: 12px">{{ selectedItem.category }}</el-tag>
              <h3>{{ selectedItem.question }}</h3>
              <el-divider />
              <div class="answer-body">{{ selectedItem.answer }}</div>
              <el-divider />
              <p class="answer-tip">如需进一步咨询制度细节，可返回智能问答使用「查制度」或「办事项」。</p>
            </template>
            <el-empty v-else description="请从左侧选择一个问题" />
          </el-card>
        </div>
      </el-col>
    </el-row>

    <!-- 管理弹窗 -->
    <el-dialog v-model="manageDialogVisible" title="管理新员工速查指引" width="900px" fullscreen>
      <div class="manage-container">
        <!-- 分类列表 -->
        <div class="manage-sidebar">
          <div class="manage-sidebar-header">
            <h4>分类列表</h4>
            <el-button type="primary" size="small" @click="showAddCategory">
              <el-icon><Plus /></el-icon> 新增分类
            </el-button>
          </div>
          <div class="category-list">
            <div
              v-for="cat in manageCategories"
              :key="cat.id"
              :class="['category-item', { active: selectedManageCategoryId === cat.id }]"
              @click="selectManageCategory(cat)"
            >
              <span>{{ cat.title }}（{{ cat.items?.length || 0 }}）</span>
              <div class="category-actions">
                <el-button text size="small" @click.stop="showEditCategory(cat)">
                  <el-icon><Edit /></el-icon>
                </el-button>
                <el-button text size="small" type="danger" @click.stop="handleDeleteCategory(cat)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <!-- 条目列表 -->
        <div class="manage-content">
          <template v-if="selectedManageCategory">
            <div class="manage-content-header">
              <h4>{{ selectedManageCategory.title }} - 条目列表</h4>
              <el-button type="primary" size="small" @click="showAddItem">
                <el-icon><Plus /></el-icon> 新增条目
              </el-button>
            </div>
            <el-table v-loading="manageLoading" :data="selectedManageCategory.items" border row-key="id">
              <el-table-column prop="question" label="问题" min-width="200" />
              <el-table-column prop="answer" label="答案" min-width="300">
                <template #default="{ row }">
                  <div class="answer-preview">{{ previewAnswer(row.answer) }}</div>
                </template>
              </el-table-column>
              <el-table-column prop="sort_order" label="排序" width="80" />
              <el-table-column label="操作" width="150">
                <template #default="{ row }">
                  <el-button text size="small" @click="showEditItem(row)">
                    <el-icon><Edit /></el-icon> 编辑
                  </el-button>
                  <el-button text size="small" type="danger" @click="handleDeleteItem(row)">
                    <el-icon><Delete /></el-icon> 删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </template>
          <el-empty v-else description="请从左侧选择一个分类" />
        </div>
      </div>

      <!-- 分类编辑弹窗 -->
      <el-dialog v-model="categoryDialogVisible" :title="isEditCategory ? '编辑分类' : '新增分类'" width="400px" append-to-body>
        <el-form :model="categoryForm" label-width="80px">
          <el-form-item label="分类标题" required>
            <el-input v-model="categoryForm.title" placeholder="请输入分类标题" />
          </el-form-item>
          <el-form-item label="排序序号">
            <el-input-number v-model="categoryForm.sort_order" :min="0" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="categoryDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSaveCategory" :loading="saving">保存</el-button>
        </template>
      </el-dialog>

      <!-- 条目编辑弹窗 -->
      <el-dialog v-model="itemDialogVisible" :title="isEditItem ? '编辑条目' : '新增条目'" width="600px" append-to-body>
        <el-form :model="itemForm" label-width="80px">
          <el-form-item label="问题" required>
            <el-input v-model="itemForm.question" placeholder="请输入问题" />
          </el-form-item>
          <el-form-item label="答案" required>
            <el-input v-model="itemForm.answer" type="textarea" :rows="6" placeholder="请输入答案" />
          </el-form-item>
          <el-form-item label="排序序号">
            <el-input-number v-model="itemForm.sort_order" :min="0" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="itemDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSaveItem" :loading="saving">保存</el-button>
        </template>
      </el-dialog>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ArrowLeft, Edit, Plus, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getGuideList, getGuideItem,
  createGuideCategory, updateGuideCategory, deleteGuideCategory,
  createGuideItem, updateGuideItem, deleteGuideItem
} from '../api/guide'

// 用户角色
const user = JSON.parse(localStorage.getItem('user') || '{}')
const isHR = computed(() => user.role === 'hr' || user.role === 'admin')

// 查看模式数据
const categories = ref([])
const activeCategories = ref([])
const selectedId = ref('')
const selectedItem = ref(null)

// 管理模式数据
const manageDialogVisible = ref(false)
const manageCategories = ref([])
const manageLoading = ref(false)
const selectedManageCategoryId = ref(null)
const selectedManageCategory = computed(() =>
  manageCategories.value.find(c => c.id === selectedManageCategoryId.value) || null
)

// 分类编辑
const categoryDialogVisible = ref(false)
const isEditCategory = ref(false)
const editingCategoryId = ref(null)
const categoryForm = ref({ title: '', sort_order: 0 })

// 条目编辑
const itemDialogVisible = ref(false)
const isEditItem = ref(false)
const editingItemId = ref(null)
const itemForm = ref({ question: '', answer: '', sort_order: 0 })

const saving = ref(false)

function previewAnswer(answer) {
  const text = answer || ''
  if (!text) return '（暂无答案）'
  return text.length > 100 ? `${text.substring(0, 100)}...` : text
}

async function enrichCategoryItems(categories) {
  const needsEnrich = categories.some(cat =>
    (cat.items || []).some(item => item.answer === undefined || item.answer === null)
  )
  if (!needsEnrich) return categories

  return Promise.all(categories.map(async (cat) => ({
    ...cat,
    items: await Promise.all((cat.items || []).map(async (item) => {
      if (item.answer !== undefined && item.answer !== null) return item
      try {
        const res = await getGuideItem(item.id)
        const data = res.data || {}
        return {
          ...item,
          question: data.question ?? item.question,
          answer: data.answer ?? '',
          sort_order: data.sort_order ?? item.sort_order ?? 0,
        }
      } catch {
        return { ...item, answer: item.answer ?? '', sort_order: item.sort_order ?? 0 }
      }
    })),
  })))
}

// ==================== 查看模式 ====================

async function loadList() {
  try {
    const res = await getGuideList()
    const list = res.data?.categories || []
    // 部门专属「新人必做事项」置顶，其余保持原序
    list.sort((a, b) => {
      const aTop = a.title.includes('新人必做事项') ? 0 : 1
      const bTop = b.title.includes('新人必做事项') ? 0 : 1
      return aTop - bTop
    })
    categories.value = list
    activeCategories.value = categories.value.map(c => c.id)
  } catch (e) {}
}

async function selectItem(id) {
  selectedId.value = id
  try {
    const res = await getGuideItem(id)
    selectedItem.value = res.data
  } catch (e) {
    selectedItem.value = null
  }
}

// ==================== 管理模式 ====================

async function openManageDialog() {
  manageDialogVisible.value = true
  await loadManageCategories()
  await loadList()
}

async function loadManageCategories() {
  manageLoading.value = true
  try {
    const res = await getGuideList(true)
    const categories = res.data?.categories || []
    manageCategories.value = await enrichCategoryItems(categories)
    if (selectedManageCategoryId.value && !manageCategories.value.some(c => c.id === selectedManageCategoryId.value)) {
      selectedManageCategoryId.value = null
    }
  } catch (e) {
    ElMessage.error('加载分类失败')
  } finally {
    manageLoading.value = false
  }
}

function selectManageCategory(cat) {
  selectedManageCategoryId.value = cat.id
}

// 分类操作
function showAddCategory() {
  isEditCategory.value = false
  editingCategoryId.value = null
  categoryForm.value = { title: '', sort_order: 0 }
  categoryDialogVisible.value = true
}

function showEditCategory(cat) {
  isEditCategory.value = true
  editingCategoryId.value = cat.id
  categoryForm.value = { title: cat.title, sort_order: cat.sort_order }
  categoryDialogVisible.value = true
}

async function handleSaveCategory() {
  if (!categoryForm.value.title) {
    ElMessage.warning('请输入分类标题')
    return
  }
  saving.value = true
  try {
    if (isEditCategory.value) {
      await updateGuideCategory(editingCategoryId.value, categoryForm.value)
      ElMessage.success('更新成功')
    } else {
      await createGuideCategory(categoryForm.value)
      ElMessage.success('创建成功')
    }
    categoryDialogVisible.value = false
    await loadManageCategories()
    await loadList()
  } catch (e) {
    ElMessage.error('操作失败')
  } finally {
    saving.value = false
  }
}

async function handleDeleteCategory(cat) {
  try {
    await ElMessageBox.confirm(`确定要删除分类"${cat.title}"吗？删除后该分类下的所有条目也会被删除。`, '确认删除', {
      type: 'warning'
    })
    await deleteGuideCategory(cat.id)
    ElMessage.success('删除成功')
    if (selectedManageCategoryId.value === cat.id) {
      selectedManageCategoryId.value = null
    }
    await loadManageCategories()
    await loadList()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

// 条目操作
function showAddItem() {
  isEditItem.value = false
  editingItemId.value = null
  itemForm.value = { question: '', answer: '', sort_order: 0 }
  itemDialogVisible.value = true
}

async function showEditItem(item) {
  isEditItem.value = true
  editingItemId.value = item.id
  if (item.answer !== undefined && item.answer !== null) {
    itemForm.value = { question: item.question, answer: item.answer, sort_order: item.sort_order ?? 0 }
    itemDialogVisible.value = true
    return
  }
  try {
    const res = await getGuideItem(item.id)
    const data = res.data || {}
    itemForm.value = {
      question: data.question ?? item.question,
      answer: data.answer ?? '',
      sort_order: data.sort_order ?? 0,
    }
  } catch {
    itemForm.value = { question: item.question, answer: '', sort_order: item.sort_order ?? 0 }
  }
  itemDialogVisible.value = true
}

async function handleSaveItem() {
  if (!itemForm.value.question || !itemForm.value.answer) {
    ElMessage.warning('请输入问题和答案')
    return
  }
  saving.value = true
  try {
    if (isEditItem.value) {
      await updateGuideItem(editingItemId.value, itemForm.value)
      ElMessage.success('更新成功')
    } else {
      await createGuideItem(selectedManageCategory.value.id, itemForm.value)
      ElMessage.success('创建成功')
    }
    itemDialogVisible.value = false
    await loadManageCategories()
    await loadList()
  } catch (e) {
    ElMessage.error('操作失败')
  } finally {
    saving.value = false
  }
}

async function handleDeleteItem(item) {
  try {
    await ElMessageBox.confirm(`确定要删除条目"${item.question}"吗？`, '确认删除', {
      type: 'warning'
    })
    await deleteGuideItem(item.id)
    ElMessage.success('删除成功')
    await loadManageCategories()
    await loadList()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

onMounted(loadList)
</script>

<style scoped>
.guide-page { max-width: 1100px; margin: 0 auto; }
.guide-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20px;
}
.header-title { flex: 1; }
.guide-header h2 { margin: 8px 0 4px; color: #111827; }
.guide-sub { color: #6b7280; font-size: 14px; margin: 0; }
.guide-item {
  padding: 10px 12px; border-radius: 8px; cursor: pointer; margin-bottom: 6px;
  color: #374151; font-size: 14px; transition: background 0.2s;
}
.guide-item:hover { background: #fff7ed; }
.left-card-wrapper {
  position: sticky;
  top: 20px;
}
.left-card {
  max-height: calc(100vh - 120px);
  overflow-y: auto;
}
.guide-item.active { background: #ffedd5; color: #92400e; font-weight: 500; }
.answer-card-wrapper {
  position: sticky;
  top: 20px;
}
.answer-card {
  min-height: 360px;
  max-height: calc(100vh - 120px);
  overflow-y: auto;
}
.answer-body { white-space: pre-wrap; line-height: 1.8; color: #374151; }
.answer-tip { color: #9ca3af; font-size: 13px; margin: 0; }

/* 管理弹窗样式 */
.manage-container {
  display: flex;
  gap: 20px;
  min-height: 500px;
}
.manage-sidebar {
  width: 250px;
  border-right: 1px solid #e5e7eb;
  padding-right: 20px;
}
.manage-sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.manage-sidebar-header h4 { margin: 0; }
.category-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.category-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}
.category-item:hover { border-color: #f59e0b; background: #fffbeb; }
.category-item.active { border-color: #f59e0b; background: #fef3c7; }
.category-actions {
  display: flex;
  gap: 4px;
}
.manage-content {
  flex: 1;
}
.manage-content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.manage-content-header h4 { margin: 0; }
.answer-preview {
  max-height: 60px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
