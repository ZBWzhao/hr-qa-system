<template>
  <el-card>
    <template #header>
      <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px">
        <span style="font-weight: 600; color: #111827">通知公告</span>
        <el-button v-if="userStore.isHR" type="primary" @click="showDialog()">发布通知</el-button>
      </div>
    </template>
    <div v-for="notice in notices" :key="notice.id" class="notice-item" @click="viewNotice(notice)">
      <div style="display: flex; justify-content: space-between; align-items: center">
        <div>
          <el-tag v-if="notice.is_pinned" type="danger" size="small" style="margin-right: 8px">置顶</el-tag>
          <el-tag v-if="!notice.is_read" type="warning" size="small" style="margin-right: 8px">未读</el-tag>
          <span style="font-size: 16px; font-weight: 500">{{ notice.title }}</span>
        </div>
        <span style="color: #9CA3AF; font-size: 12px">{{ notice.created_at?.substring(0, 10) }}</span>
      </div>
      <div style="color: #6B7280; margin-top: 8px; font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap">{{ notice.content }}</div>
    </div>
    <el-empty v-if="!notices.length" description="暂无通知" />
    <el-pagination style="margin-top: 16px; justify-content: center" :current-page="page" :page-size="20" :total="total" layout="prev, pager, next" @current-change="p => { page = p; fetchData() }" />

    <el-drawer v-model="detailVisible" title="通知详情" size="50%">
      <h3>{{ detail.title }}</h3>
      <div style="color: #9CA3AF; margin: 8px 0">发布时间：{{ detail.created_at?.substring(0, 10) }}</div>
      <el-divider />
      <div style="white-space: pre-wrap; line-height: 1.8">{{ detail.content }}</div>
    </el-drawer>

    <el-dialog v-model="dialogVisible" title="发布通知" width="600px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="内容"><el-input v-model="form.content" type="textarea" :rows="8" /></el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.notice_type">
            <el-option label="一般" value="general" />
            <el-option label="政策" value="policy" />
            <el-option label="假期" value="holiday" />
            <el-option label="提醒" value="reminder" />
          </el-select>
        </el-form-item>
        <el-form-item label="置顶"><el-switch v-model="form.is_pinned" :active-value="1" :inactive-value="0" /></el-form-item>
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
import { ElMessage } from 'element-plus'
import { getNotices, getNotice, createNotice } from '../api/notices'
import { useUserStore } from '../stores/user'
import { useRouter } from 'vue-router'

const userStore = useUserStore()
const router = useRouter()
const notices = ref([])
const page = ref(1)
const total = ref(0)
const detailVisible = ref(false)
const detail = ref({})
const dialogVisible = ref(false)
const form = reactive({ title: '', content: '', notice_type: 'general', is_pinned: 0 })

async function fetchData() {
  try {
    const res = await getNotices({ page: page.value })
    notices.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch (e) {}
}

async function viewNotice(notice) {
  try {
    const res = await getNotice(notice.id)
    detail.value = res.data
    notice.is_read = true
    detailVisible.value = true
    // 刷新Layout中的未读数
    const layout = router.currentRoute.value.matched[0]?.instances?.default
    if (layout?.fetchUnread) layout.fetchUnread()
  } catch (e) {}
}

function showDialog() {
  Object.assign(form, { title: '', content: '', notice_type: 'general', is_pinned: 0 })
  dialogVisible.value = true
}

async function handleSubmit() {
  await createNotice(form)
  ElMessage.success('发布成功')
  dialogVisible.value = false
  fetchData()
}

onMounted(() => fetchData())
</script>

<style scoped>
.notice-item { padding: 16px; border: 1px solid #f3f4f6; border-radius: 12px; margin-bottom: 12px; cursor: pointer; transition: all 0.3s; }
.notice-item:hover { border-color: #D97706; box-shadow: 0 2px 8px rgba(217, 119, 6, 0.08); }
</style>
