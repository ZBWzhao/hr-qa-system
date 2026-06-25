<template>
  <div>
    <el-row :gutter="20" style="margin-bottom: 20px">
      <el-col :span="6" v-for="card in statCards" :key="card.title">
        <el-card shadow="hover" style="cursor: pointer" @click="card.action && card.action()">
          <div style="display: flex; align-items: center; justify-content: space-between">
            <div>
              <div style="color: #999; font-size: 14px">{{ card.title }}</div>
              <div style="font-size: 28px; font-weight: 700; margin-top: 8px; color: #333">{{ card.value }}</div>
            </div>
            <el-icon :size="48" :color="card.color"><component :is="card.icon" /></el-icon>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header><span style="font-weight: 700">猜你想问</span></template>
          <div v-for="(item, idx) in recommendations" :key="idx" style="padding: 10px 0; border-bottom: 1px solid #f0f0f0; cursor: pointer" @click="goChat(item.question)">
            <el-icon style="margin-right: 8px; color: #1890ff"><ChatDotRound /></el-icon>
            <span>{{ item.question }}</span>
            <el-tag v-if="item.type === 'faq'" size="small" style="margin-left: 8px">FAQ</el-tag>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header><span style="font-weight: 700">最新通知</span></template>
          <div v-for="notice in notices" :key="notice.id" style="padding: 10px 0; border-bottom: 1px solid #f0f0f0">
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span style="cursor: pointer; color: #333" @click="$router.push('/notices')">
                <el-tag v-if="notice.is_pinned" type="danger" size="small" style="margin-right: 8px">置顶</el-tag>
                {{ notice.title }}
              </span>
              <span style="color: #999; font-size: 12px">{{ formatDate(notice.created_at) }}</span>
            </div>
          </div>
          <el-empty v-if="!notices.length" description="暂无通知" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px" v-if="userStore.userInfo.role === 'employee'">
      <el-col :span="12">
        <el-card>
          <template #header><span style="font-weight: 700">我的工单</span></template>
          <div v-for="ticket in tickets" :key="ticket.id" style="padding: 10px 0; border-bottom: 1px solid #f0f0f0">
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>{{ ticket.title }}</span>
              <el-tag :type="ticketStatusType(ticket.status)">{{ ticketStatusLabel(ticket.status) }}</el-tag>
            </div>
          </div>
          <el-empty v-if="!tickets.length" description="暂无工单" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header><span style="font-weight: 700">我的提醒</span></template>
          <div v-for="(r, idx) in reminders" :key="idx" style="padding: 10px 0; border-bottom: 1px solid #f0f0f0">
            <el-icon style="margin-right: 8px; color: #e6a23c"><AlarmClock /></el-icon>
            <span>{{ r.message }}</span>
          </div>
          <el-empty v-if="!reminders.length" description="暂无提醒" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px" v-if="userStore.isHR">
      <el-col :span="12">
        <el-card>
          <template #header><span style="font-weight: 700">待处理工单</span></template>
          <div v-for="ticket in tickets" :key="ticket.id" style="padding: 10px 0; border-bottom: 1px solid #f0f0f0">
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>{{ ticket.title }}</span>
              <el-tag :type="ticketStatusType(ticket.status)">{{ ticketStatusLabel(ticket.status) }}</el-tag>
            </div>
          </div>
          <el-empty v-if="!tickets.length" description="暂无待处理工单" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header><span style="font-weight: 700">知识缺口</span></template>
          <div style="text-align: center; padding: 20px">
            <div style="font-size: 36px; color: #e6a23c; font-weight: 700">{{ gapStats.unresolved || 0 }}</div>
            <div style="color: #999; margin-top: 8px">未解决问题数</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { getRecommendations } from '../api/recommendations'
import { getNotices } from '../api/notices'
import { getTickets } from '../api/tickets'
import { getReminders } from '../api/reminders'
import { getGapStats } from '../api/gaps'

const router = useRouter()
const userStore = useUserStore()
const recommendations = ref([])
const notices = ref([])
const tickets = ref([])
const reminders = ref([])
const gapStats = ref({})

const statCards = computed(() => {
  if (userStore.isAdmin) {
    return [
      { title: '用户数量', value: '—', icon: 'User', color: '#1890ff' },
      { title: '部门数量', value: '—', icon: 'OfficeBuilding', color: '#52c41a' },
      { title: '文档数量', value: '—', icon: 'Document', color: '#faad14' },
      { title: '系统状态', value: '正常', icon: 'CircleCheck', color: '#52c41a' }
    ]
  }
  return [
    { title: '智能问答', value: '进入', icon: 'ChatDotRound', color: '#1890ff', action: () => router.push('/chat') },
    { title: '制度文档', value: '查看', icon: 'Document', color: '#52c41a', action: () => router.push(userStore.isHR ? '/documents' : '/search') },
    { title: '通知公告', value: notices.value.length, icon: 'Bell', color: '#faad14' },
    { title: '我的工单', value: tickets.value.length, icon: 'Tickets', color: '#722ed1' }
  ]
})

function ticketStatusType(s) {
  return { pending: 'warning', processing: 'primary', completed: 'success', rejected: 'danger' }[s] || 'info'
}
function ticketStatusLabel(s) {
  return { pending: '待处理', processing: '处理中', completed: '已完成', rejected: '已驳回' }[s] || s
}
function formatDate(d) {
  return d ? d.substring(0, 10) : ''
}
function goChat(q) {
  router.push({ path: '/chat', query: { q } })
}

onMounted(async () => {
  try { const res = await getRecommendations(); recommendations.value = res.data || [] } catch (e) {}
  try { const res = await getNotices({ page_size: 5 }); notices.value = res.data?.items || [] } catch (e) {}
  try { const res = await getTickets({ page_size: 5 }); tickets.value = res.data?.items || [] } catch (e) {}
  try { const res = await getReminders(); reminders.value = (res.data || []).slice(0, 5) } catch (e) {}
  try { const res = await getGapStats(); gapStats.value = res.data || {} } catch (e) {}
})
</script>
