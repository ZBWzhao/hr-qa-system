<template>
  <el-card>
    <template #header>
      <div style="display: flex; justify-content: space-between; align-items: center">
        <span style="font-weight: 700">规则问答管理</span>
        <el-button type="primary" @click="showDialog()">新增规则</el-button>
      </div>
    </template>
    <el-table :data="rules" v-loading="loading" stripe>
      <el-table-column prop="name" label="规则名称" min-width="150" />
      <el-table-column prop="trigger_keywords" label="触发关键词" min-width="200" />
      <el-table-column prop="category" label="分类" width="100" />
      <el-table-column prop="priority" label="优先级" width="80" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">{{ row.status === 1 ? '启用' : '禁用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="250">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="showDialog(row)">编辑</el-button>
          <el-button size="small" :type="row.status === 1 ? 'warning' : 'success'" @click="toggleStatus(row)">{{ row.status === 1 ? '禁用' : '启用' }}</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination style="margin-top: 16px; justify-content: center" :current-page="page" :page-size="20" :total="total" layout="prev, pager, next" @current-change="p => { page = p; fetchData() }" />

    <el-dialog v-model="dialogVisible" :title="editId ? '编辑规则' : '新增规则'" width="600px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="规则名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="触发关键词"><el-input v-model="form.trigger_keywords" placeholder="用逗号分隔" /></el-form-item>
        <el-form-item label="回答模板"><el-input v-model="form.answer_template" type="textarea" :rows="6" /></el-form-item>
        <el-form-item label="分类"><el-input v-model="form.category" /></el-form-item>
        <el-form-item label="优先级"><el-input-number v-model="form.priority" :min="0" :max="100" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getRules, createRule, updateRule, deleteRule } from '../api/rules'

const loading = ref(false)
const rules = ref([])
const page = ref(1)
const total = ref(0)
const dialogVisible = ref(false)
const editId = ref(null)
const form = reactive({ name: '', trigger_keywords: '', answer_template: '', category: '', priority: 0 })

async function fetchData() {
  loading.value = true
  try {
    const res = await getRules({ page: page.value })
    rules.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch (e) {} finally { loading.value = false }
}

function showDialog(row) {
  editId.value = row?.id || null
  if (row) {
    Object.assign(form, row)
  } else {
    Object.assign(form, { name: '', trigger_keywords: '', answer_template: '', category: '', priority: 0 })
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  try {
    if (editId.value) {
      await updateRule(editId.value, form)
    } else {
      await createRule(form)
    }
    ElMessage.success('操作成功')
    dialogVisible.value = false
    fetchData()
  } catch (e) {}
}

async function toggleStatus(row) {
  await updateRule(row.id, { status: row.status === 1 ? 0 : 1 })
  ElMessage.success('操作成功')
  fetchData()
}

async function handleDelete(row) {
  await ElMessageBox.confirm('确认删除？', '提示', { type: 'warning' })
  await deleteRule(row.id)
  ElMessage.success('删除成功')
  fetchData()
}

onMounted(() => fetchData())
</script>