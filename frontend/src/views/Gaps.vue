<template>

  <el-card>

    <template #header><span style="font-weight: 600; color: #111827">知识缺口分析</span></template>

    <el-row :gutter="20" style="margin-bottom: 20px">

      <el-col :xs="12" :sm="12" :md="8">

        <el-statistic title="总未命中数" :value="stats.total || 0" />

      </el-col>

      <el-col :xs="12" :sm="12" :md="8">

        <el-statistic title="未解决" :value="stats.unresolved || 0" />

      </el-col>

      <el-col :xs="12" :sm="12" :md="8">

        <el-statistic title="已解决" :value="stats.resolved || 0" />

      </el-col>

    </el-row>



    <el-card shadow="never" style="margin-bottom: 20px; background: #f8fafc; border: 1px solid #e5e7eb">

      <template #header>

        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px">

          <span style="font-weight: 600">AI 知识缺口分析</span>

          <div style="display: flex; gap: 8px; align-items: center">

            <el-text v-if="analysisUpdatedAt" type="info" size="small">更新于 {{ analysisUpdatedAt.substring(0, 16).replace('T', ' ') }}</el-text>

            <el-button type="primary" size="small" :loading="analysisLoading" @click="handleGenerateAnalysis">

              {{ gapAnalysis ? '刷新分析' : '生成 AI 分析' }}

            </el-button>

          </div>

        </div>

      </template>

      <div v-loading="analysisLoading">

        <p v-if="!gapAnalysis" style="color: #6b7280; margin: 0">点击「生成 AI 分析」后，系统将汇总所有未解决缺口并给出分类建议（结果会缓存，避免重复调用）。</p>

        <div v-else class="gap-analysis-content" v-html="renderSimpleMarkdown(gapAnalysis)" />

      </div>

    </el-card>



    <el-table :data="gaps" v-loading="loading" stripe>

      <el-table-column prop="question" label="未命中问题" min-width="260" />

      <el-table-column prop="user_name" label="提问人" width="100" />

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

import { getGaps, getGapStats, resolveGap, getGapAnalysis, generateGapAnalysis } from '../api/gaps'
import { renderSimpleMarkdown } from '../utils/markdown'



const loading = ref(false)

const gaps = ref([])

const page = ref(1)

const total = ref(0)

const stats = ref({})

const gapAnalysis = ref('')

const analysisLoading = ref(false)

const analysisUpdatedAt = ref('')

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



async function fetchAnalysis() {

  try {

    const res = await getGapAnalysis()

    gapAnalysis.value = res.data?.content || ''

    analysisUpdatedAt.value = res.data?.updated_at || ''

  } catch (e) {}

}



async function handleGenerateAnalysis() {

  analysisLoading.value = true

  try {

    const res = await generateGapAnalysis()

    gapAnalysis.value = res.data?.content || ''

    analysisUpdatedAt.value = res.data?.updated_at || ''

    ElMessage.success(res.data?.cached ? '已读取缓存分析' : 'AI 分析已生成')

  } catch (e) {

    ElMessage.error('生成分析失败')

  } finally {

    analysisLoading.value = false

  }

}



async function handleResolve(row) {

  await resolveGap(row.id)

  ElMessage.success('已标记为已解决')

  fetchData()

  fetchStats()

  gapAnalysis.value = ''

}



onMounted(() => { fetchData(); fetchStats(); fetchAnalysis() })

</script>



<style scoped>

.gap-analysis-content {

  line-height: 1.8;

  color: #374151;

}

</style>

