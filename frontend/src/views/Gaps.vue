<template>
  <el-card>
    <template #header><span style="font-weight: 700">知识缺口分析</span></template>
    <el-row :gutter="20" style="margin-bottom: 20px">
      <el-col :span="8">
        <el-statistic title="总未命中数" :value="stats.total || 0" />
      </el-col>
      <el-col :span="8">
        <el-statistic title="未解决" :value="stats.unresolved || 0" />
      </el-col>
      <el-col :span="8">
        <el-statistic title="已解决" :value="stats.resolved || 0" />
      </el-col>
    </el-row>
    <el-alert :title="stats.suggestion || '建议针对高频未命中问题，补充相应的制度文档或FAQ'" type="info" :closable="false" style="margin-bottom: 16px" />

    <el-table :data="gaps" v-loading="loading" stripe>
      <el-table-column prop="question" label="未命中问题" min-width="300" />
      <el-table-column prop="created_at" label="时间" width="120">
        <template #default="{ row }">{{ row.created_at?.substring(0, 10) }}</template>
      </el-table-column>
      <el-table-column prop="resolved" label="状态" width="100">
        <template #default="{ row }"><el-tag :type="row.resolved ? 'success' : 'warning'" size="small">{{ row.resolved ? '已解决' : '未解决' }}</el-tag></template>
      </el-table-column>
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button v-if="!row.resolved" size="small" type="success" @click="handleResolve(row)">标记解决</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination style="margin-top: 16px; justify-content: center" :current-page="page" :page-size="20" :total="total" layout="prev, pager, next" @current-change="p => { page = p; fetchData() }" />
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getGaps, getGapStats, resolveGap } from '../api/gaps'

const loading = ref(false)
const gaps = ref([])
const page = ref(1)
const total = ref(0)
const stats = ref({})

async function fetchData() {
  loading.value = true
  try {
    const res = await getGaps({ page: page.value })
    gaps.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch (e) {} finally { loading.value = false }
}

async function fetchStats() {
  try {
    const res = await getGapStats()
    stats.value = res.data || {}
  } catch (e) {}
}

async function handleResolve(row) {
  await resolveGap(row.id)
  ElMessage.success('已标记为已解决')
  fetchData()
  fetchStats()
}

onMounted(() => { fetchData(); fetchStats() })
</script>
