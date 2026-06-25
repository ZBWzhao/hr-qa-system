<template>
  <div>
    <el-row :gutter="20" style="margin-bottom: 20px">
      <el-col :span="6" v-for="card in statCards" :key="card.title">
        <el-card shadow="hover" style="cursor: pointer; border-radius: 12px" @click="card.action && card.action()">
          <div style="display: flex; align-items: center; justify-content: space-between">
            <div>
              <div style="color: #9CA3AF; font-size: 13px; font-weight: 500">{{ card.title }}</div>
              <div style="font-size: 28px; font-weight: 700; margin-top: 8px; color: #111827">{{ card.value }}</div>
            </div>
            <el-icon :size="44" :color="card.color"><component :is="card.icon" /></el-icon>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header><span style="font-weight: 600; color: #111827">猜你想问</span></template>
          <div v-for="(item, idx) in recommendations" :key="idx" style="padding: 10px 0; border-bottom: 1px solid #f3f4f6; cursor: pointer" @click="goChat(item.question)">
            <el-icon style="margin-right: 8px; color: #D97706"><ChatDotRound /></el-icon>
            <span style="color: #374151">{{ item.question }}</span>
            <el-tag v-if="item.type === 'faq'" size="small" style="margin-left: 8px">FAQ</el-tag>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header><span style="font-weight: 600; color: #111827">最新通知</span></template>
          <div v-for="notice in notices" :key="notice.id" style="padding: 10px 0; border-bottom: 1px solid #f3f4f6">
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span style="cursor: pointer; color: #374151" @click="$router.push('/notices')">
                <el-tag v-if="notice.is_pinned" type="danger" size="small" style="margin-right: 8px">置顶</el-tag>
                {{ notice.title }}
              </span>
              <span style="color: #9CA3AF; font-size: 12px">{{ formatDate(notice.created_at) }}</span>
            </div>
          </div>
          <el-empty v-if="!notices.length" description="暂无通知" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px" v-if="userStore.userInfo.role === 'employee'">
      <el-col :span="12">
        <el-card>
          <template #header><span style="font-weight: 600; color: #111827">我的工单</span></template>
          <div v-for="ticket in tickets" :key="ticket.id" style="padding: 10px 0; border-bottom: 1px solid #f3f4f6">
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span style="color: #374151">{{ ticket.title }}</span>
              <el-tag :type="ticketStatusType(ticket.status)">{{ ticketStatusLabel(ticket.status) }}</el-tag>
            </div>
          </div>
          <el-empty v-if="!tickets.length" description="暂无工单" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header><span style="font-weight: 600; color: #111827">我的提醒</span></template>
          <div v-for="(r, idx) in reminders" :key="idx" style="padding: 10px 0; border-bottom: 1px solid #f3f4f6">
            <el-icon style="margin-right: 8px; color: #D97706"><AlarmClock /></el-icon>
            <span style="color: #374151">{{ r.message }}</span>
          </div>
          <el-empty v-if="!reminders.length" description="暂无提醒" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px" v-if="userStore.isHR">
      <el-col :span="12">
        <el-card>
          <template #header><span style="font-weight: 600; color: #111827">待处理工单</span></template>
          <div v-for="ticket in tickets" :key="ticket.id" style="padding: 10px 0; border-bottom: 1px solid #f3f4f6">
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span style="color: #374151">{{ ticket.title }}</span>
              <el-tag :type="ticketStatusType(ticket.status)">{{ ticketStatusLabel(ticket.status) }}</el-tag>
            </div>
          </div>
          <el-empty v-if="!tickets.length" description="暂无待处理工单" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header><span style="font-weight: 600; color: #111827">知识缺口</span></template>
          <div style="text-align: center; padding: 20px">
            <div style="font-size: 36px; color: #D97706; font-weight: 700">{{ gapStats.unresolved || 0 }}</div>
            <div style="color: #9CA3AF; margin-top: 8px">未解决问题数</div>
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
      { title: '用户数量', value: '—', icon: 'User', color: '#D97706' },
      { title: '部门数量', value: '—', icon: 'OfficeBuilding', color: '#059669' },
      { title: '文档数量', value: '—', icon: 'Document', color: '#D97706' },
      { title: '系统状态', value: '正常', icon: 'CircleCheck', color: '#059669' }
    ]
  }
  return [
    { title: '智能问答', value: '进入', icon: 'ChatDotRound', color: '#D97706', action: () => router.push('/chat') },
    { title: '制度文档', value: '查看', icon: 'Document', color: '#059669', action: () => router.push(userStore.isHR ? '/documents' : '/search') },
    { title: '通知公告', value: notices.value.length, icon: 'Bell', color: '#D97706' },
    { title: '我的工单', value: tickets.value.length, icon: 'Tickets', color: '#6B7280' }
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
