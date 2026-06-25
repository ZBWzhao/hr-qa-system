<template>
  <el-card>
    <template #header>
      <div style="display: flex; justify-content: space-between; align-items: center">
        <span style="font-weight: 700">部门管理</span>
        <el-button type="primary" @click="showDialog()">新增部门</el-button>
      </div>
    </template>
    <el-table :data="departments" row-key="id" default-expand-all v-loading="loading">
      <el-table-column prop="name" label="部门名称" min-width="200" />
      <el-table-column prop="sort_order" label="排序" width="100" />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="showDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editId ? '编辑部门' : '新增部门'" width="400px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="上级部门">
          <el-tree-select v-model="form.parent_id" :data="departments" :props="{ label: 'name', value: 'id', children: 'children' }" check-strictly clearable placeholder="无" style="width: 100%" />
        </el-form-item>
        <el-form-item label="排序"><el-input-number v-model="form.sort_order" :min="0" /></el-form-item>
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
import { getDepartments, createDepartment, updateDepartment, deleteDepartment } from '../api/departments'

const loading = ref(false)
const departments = ref([])
const dialogVisible = ref(false)
const editId = ref(null)
const form = reactive({ name: '', parent_id: null, sort_order: 0 })

async function fetchData() {
  loading.value = true
  try {
    const res = await getDepartments()
    departments.value = res.data || []
  } catch (e) {} finally { loading.value = false }
}

function showDialog(row) {
  editId.value = row?.id || null
  if (row) {
    Object.assign(form, { name: row.name, parent_id: row.parent_id, sort_order: row.sort_order })
  } else {
    Object.assign(form, { name: '', parent_id: null, sort_order: 0 })
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  if (editId.value) {
    await updateDepartment(editId.value, form)
  } else {
    await createDepartment(form)
  }
  ElMessage.success('操作成功')
  dialogVisible.value = false
  fetchData()
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确认删除部门「${row.name}」？`, '提示', { type: 'warning' })
  await deleteDepartment(row.id)
  ElMessage.success('删除成功')
  fetchData()
}

onMounted(() => fetchData())
</script>
