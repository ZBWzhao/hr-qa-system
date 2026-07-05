<template>
  <div>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="数据总览" name="overview">
        <el-row :gutter="20">
          <!-- 问答量趋势 -->
          <el-col :xs="24" :sm="24" :md="6" style="margin-bottom: 20px">
            <el-card>
              <template #header>
                <span style="font-weight: 600; color: #111827">问答量趋势</span>
              </template>
              <div ref="qaTrendChart" style="height: 320px"></div>
            </el-card>
          </el-col>

          <!-- 咨询类别分布 -->
          <el-col :xs="24" :sm="24" :md="6" style="margin-bottom: 20px">
            <el-card>
              <template #header>
                <span style="font-weight: 600; color: #111827">咨询类别分布</span>
              </template>
              <div ref="categoryDistChart" style="height: 320px"></div>
            </el-card>
          </el-col>

          <!-- 高频问题排行（带AI分析 + 可编辑推荐） -->
          <el-col :xs="24" :sm="24" :md="12" style="margin-bottom: 20px">
            <el-card>
              <template #header>
                <div class="chart-header">
                  <span style="font-weight: 600; color: #111827">高频问题排行</span>
                  <el-button size="small" type="primary" plain :loading="analysisLoading.top_questions_guide" @click="handleTopQuestionsGuideAnalysis">
                    {{ analyses.top_questions_guide ? '刷新速查推荐' : '速查指引推荐' }}
                  </el-button>
                </div>
              </template>
              <div ref="topQuestionsChart" style="height: 320px"></div>
              <!-- AI 分析摘要 -->
              <el-collapse v-if="analyses.top_questions_guide" style="margin-top: 12px">
                <el-collapse-item title="AI 速查指引推荐分析" name="1">
                  <div class="md-content" style="line-height: 1.8" v-html="renderSimpleMarkdown(analyses.top_questions_guide)"></div>
                </el-collapse-item>
              </el-collapse>
              <!-- 可编辑推荐条目列表 -->
              <div v-if="guideRecommendations.length" style="margin-top: 12px">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px">
                  <span style="font-size: 14px; font-weight: 600; color: #111827">推荐条目（可编辑）</span>
                  <div style="display: flex; gap: 6px">
                    <el-button size="small" @click="toggleAllRecommendations">{{ allRecommendationsSelected ? '取消全选' : '全选' }}</el-button>
                    <el-button size="small" type="danger" plain @click="guideRecommendations = []">清空</el-button>
                  </div>
                </div>
                <div v-for="(item, index) in guideRecommendations" :key="index" style="border: 1px solid #E5E7EB; border-radius: 8px; padding: 12px; margin-bottom: 8px; background: #FAFAFA">
                  <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px">
                    <el-switch v-model="item.enabled" size="small" style="flex-shrink: 0" />
                    <el-button size="small" type="danger" text @click="guideRecommendations.splice(index, 1)">移除</el-button>
                  </div>
                  <el-input v-model="item.question" size="small" placeholder="问题" style="margin-bottom: 6px" />
                  <el-input v-model="item.suggested_answer" type="textarea" :rows="2" size="small" placeholder="建议答案" style="margin-bottom: 6px" />
                  <el-select v-model="item.category_id" size="small" placeholder="选择目标分类" style="width: 100%">
                    <el-option v-for="cat in guideCategories" :key="cat.id" :label="cat.title" :value="cat.id" />
                  </el-select>
                </div>
                <el-button type="primary" size="small" style="width: 100%; margin-top: 4px" :loading="importLoading" :disabled="!enabledRecommendations.length" @click="handleBatchImport">
                  批量导入指引（{{ enabledRecommendations.length }} 条）
                </el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <el-tab-pane label="工单分析" name="tickets">
        <el-row :gutter="20">
          <!-- 工单类型分布（按部门筛选） -->
          <el-col :xs="24" :sm="24" :md="12" style="margin-bottom: 20px">
            <el-card>
              <template #header>
                <div class="chart-header">
                  <span style="font-weight: 600; color: #111827">工单类型分布</span>
                  <div class="filter-group">
                    <el-select v-model="selectedDeptForType" placeholder="选择部门" clearable size="small" @change="loadTicketByTypeByDept">
                      <el-option label="全部门" :value="null" />
                      <el-option v-for="dept in departments" :key="dept.id" :label="dept.name" :value="dept.id" />
                    </el-select>
                    <el-button size="small" type="primary" plain :loading="analysisLoading.type_by_dept" @click="handleTicketByTypeAnalysis">
                      {{ analyses.type_by_dept ? '刷新 AI 分析' : 'AI 分析' }}
                    </el-button>
                  </div>
                </div>
              </template>
              <div ref="ticketByTypeByDeptChart" style="height: 320px"></div>
              <el-collapse v-if="analyses.type_by_dept" style="margin-top: 12px">
                <el-collapse-item title="AI 数据解读与建议" name="1">
                  <div class="md-content" style="line-height: 1.8" v-html="renderSimpleMarkdown(analyses.type_by_dept)"></div>
                </el-collapse-item>
              </el-collapse>
            </el-card>
          </el-col>

          <!-- 工单部门分布（按类型筛选） -->
          <el-col :xs="24" :sm="24" :md="12" style="margin-bottom: 20px">
            <el-card>
              <template #header>
                <div class="chart-header">
                  <span style="font-weight: 600; color: #111827">工单部门分布</span>
                  <div class="filter-group">
                    <el-select v-model="selectedTypeForDept" placeholder="选择工单类型" clearable size="small" @change="loadTicketByDeptByType">
                      <el-option label="全部类型" :value="null" />
                      <el-option label="证明开具" value="certify" />
                      <el-option label="信息变更" value="info_change" />
                      <el-option label="考勤异常" value="attendance_exception" />
                      <el-option label="其他" value="other" />
                    </el-select>
                    <el-button size="small" type="primary" plain :loading="analysisLoading.dept_by_type" @click="handleTicketByDeptAnalysis">
                      {{ analyses.dept_by_type ? '刷新 AI 分析' : 'AI 分析' }}
                    </el-button>
                  </div>
                </div>
              </template>
              <div ref="ticketByDeptByTypeChart" style="height: 320px"></div>
              <el-collapse v-if="analyses.dept_by_type" style="margin-top: 12px">
                <el-collapse-item title="AI 数据解读与建议" name="1">
                  <div class="md-content" style="line-height: 1.8" v-html="renderSimpleMarkdown(analyses.dept_by_type)"></div>
                </el-collapse-item>
              </el-collapse>
            </el-card>
          </el-col>

          <!-- 工单状态分布 -->
          <el-col :xs="24" :sm="24" :md="12" style="margin-bottom: 20px">
            <el-card>
              <template #header>
                <div class="chart-header">
                  <span style="font-weight: 600; color: #111827">工单状态分布</span>
                  <el-button size="small" type="primary" plain :loading="analysisLoading.ticket_status" @click="handleTicketStatusAnalysis">
                    {{ analyses.ticket_status ? '刷新 AI 分析' : 'AI 分析' }}
                  </el-button>
                </div>
              </template>
              <div ref="ticketStatusChart" style="height: 320px"></div>
              <el-collapse v-if="analyses.ticket_status" style="margin-top: 12px">
                <el-collapse-item title="AI 数据解读与建议" name="1">
                  <div class="md-content" style="line-height: 1.8" v-html="renderSimpleMarkdown(analyses.ticket_status)"></div>
                </el-collapse-item>
              </el-collapse>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <el-tab-pane label="ROI分析" name="roi">
        <el-row :gutter="20" style="margin-bottom: 20px">
          <el-col :xs="12" :sm="12" :md="6">
            <el-card shadow="hover"><el-statistic title="本月问答量" :value="roiReport.month_qa || 0" /></el-card>
          </el-col>
          <el-col :xs="12" :sm="12" :md="6">
            <el-card shadow="hover"><el-statistic title="本月节省工时(h)" :value="roiReport.month_saved_hours || 0" /></el-card>
          </el-col>
          <el-col :xs="12" :sm="12" :md="6">
            <el-card shadow="hover"><el-statistic title="等效全职HR" :value="roiReport.equivalent_fte || 0" /></el-card>
          </el-col>
          <el-col :xs="12" :sm="12" :md="6">
            <el-card shadow="hover"><el-statistic title="ROI百分比" :value="roiReport.roi_percentage || 0" suffix="%" /></el-card>
          </el-col>
        </el-row>
        <el-card>
          <template #header><span style="font-weight: 600; color: #111827">ROI分析报告</span></template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="总问答量">{{ roiReport.total_qa }}</el-descriptions-item>
            <el-descriptions-item label="本月问答量">{{ roiReport.month_qa }}</el-descriptions-item>
            <el-descriptions-item label="总工单量">{{ roiReport.total_tickets }}</el-descriptions-item>
            <el-descriptions-item label="本月工单量">{{ roiReport.month_tickets }}</el-descriptions-item>
            <el-descriptions-item label="总节省工时">{{ roiReport.total_saved_hours }} 小时</el-descriptions-item>
            <el-descriptions-item label="本月节省工时">{{ roiReport.month_saved_hours }} 小时</el-descriptions-item>
          </el-descriptions>
          <el-divider />
          <div style="padding: 16px; background: #ECFDF5; border-radius: 12px; color: #059669; font-size: 16px">{{ roiReport.report_summary }}</div>
          <div ref="roiChartRef" style="height: 300px; margin-top: 20px"></div>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import {
  getChartData, getChartAnalysis, generateChartAnalysis,
  getDepartments, getTicketByTypeByDept, getTicketByDeptByType,
  generateTicketByTypeByDeptAnalysis, generateTicketByDeptByTypeAnalysis,
  generateTopQuestionsGuideAnalysis
} from '../api/statistics'
import { getRoiReport } from '../api/roi'
import { renderSimpleMarkdown } from '../utils/markdown'
import { getGuideCategories, batchImportGuideItems } from '../api/guide'

const activeTab = ref('overview')
const chartInstances = {}
const analyses = reactive({})
const analysisLoading = reactive({})

// 部门列表
const departments = ref([])

// 筛选状态
const selectedDeptForType = ref(null)
const selectedTypeForDept = ref(null)

// ROI数据
const roiReport = ref({})
const roiChartRef = ref(null)

// 速查指引推荐
const guideRecommendations = ref([])
const guideCategories = ref([])
const importLoading = ref(false)

const enabledRecommendations = computed(() =>
  guideRecommendations.value.filter(r => r.enabled && r.question.trim() && r.suggested_answer.trim())
)
const allRecommendationsSelected = computed(() =>
  guideRecommendations.value.length > 0 && guideRecommendations.value.every(r => r.enabled)
)

// 数据总览图表引用
const qaTrendChart = ref(null)
const categoryDistChart = ref(null)
const topQuestionsChart = ref(null)

// 筛选图表引用
const ticketByTypeByDeptChart = ref(null)
const ticketByDeptByTypeChart = ref(null)
const ticketStatusChart = ref(null)

// 渲染问答量趋势
async function renderQaTrend() {
  await nextTick()
  const el = qaTrendChart.value
  if (!el) return
  if (chartInstances.qa_trend) chartInstances.qa_trend.dispose()
  const chart = echarts.init(el)
  chartInstances.qa_trend = chart
  try {
    const res = await getChartData('qa_trend')
    const data = res.data?.data || []
    chart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: data.map(d => d.date) },
      yAxis: { type: 'value', minInterval: 1 },
      series: [{ data: data.map(d => d.count), type: 'line', smooth: true, areaStyle: { opacity: 0.3 }, itemStyle: { color: '#D97706' } }],
    })
  } catch (e) {
    chart.setOption({ title: { text: '暂无数据', left: 'center', top: 'middle', textStyle: { color: '#9CA3AF', fontSize: 14 } } })
  }
}

// 渲染咨询类别分布
async function renderCategoryDist() {
  await nextTick()
  const el = categoryDistChart.value
  if (!el) return
  if (chartInstances.category_dist) chartInstances.category_dist.dispose()
  const chart = echarts.init(el)
  chartInstances.category_dist = chart
  try {
    const res = await getChartData('category_dist')
    const data = res.data?.data || []
    chart.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { bottom: 0, type: 'scroll' },
      series: [{
        type: 'pie', radius: ['40%', '70%'],
        label: { show: true, formatter: '{b}: {c}' },
        data: data.map(d => ({ name: d.name, value: d.value })),
      }],
    })
  } catch (e) {
    chart.setOption({ title: { text: '暂无数据', left: 'center', top: 'middle', textStyle: { color: '#9CA3AF', fontSize: 14 } } })
  }
}

// 渲染高频问题排行
async function renderTopQuestions() {
  await nextTick()
  const el = topQuestionsChart.value
  if (!el) return
  if (chartInstances.top_questions) chartInstances.top_questions.dispose()
  const chart = echarts.init(el)
  chartInstances.top_questions = chart
  try {
    const res = await getChartData('top_questions')
    const data = res.data?.data || []
    const items = data.slice().sort((a, b) => a.count - b.count)
    chart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 8, right: 24, top: 8, bottom: 8, containLabel: true },
      xAxis: { type: 'value', minInterval: 1 },
      yAxis: { type: 'category', data: items.map(i => (i.question?.length > 14 ? i.question.substring(0, 14) + '…' : i.question)) },
      series: [{ type: 'bar', data: items.map(i => i.count), itemStyle: { color: '#059669' }, barMaxWidth: 22 }],
    })
  } catch (e) {
    chart.setOption({ title: { text: '暂无数据', left: 'center', top: 'middle', textStyle: { color: '#9CA3AF', fontSize: 14 } } })
  }
}

// 高频问题速查指引推荐分析
async function handleTopQuestionsGuideAnalysis() {
  analysisLoading.top_questions_guide = true
  try {
    const res = await generateTopQuestionsGuideAnalysis()
    analyses.top_questions_guide = res.data?.content || ''
    // 填充结构化推荐数据
    const recs = res.data?.recommendations || []
    console.log('[guide_analysis] res.data:', res.data)
    console.log('[guide_analysis] recommendations:', recs)
    guideRecommendations.value = recs.map(r => ({
      question: r.question || '',
      reason: r.reason || '',
      suggested_answer: r.suggested_answer || '',
      category_id: null,
      enabled: true,
    }))
    // 加载指引分类（如尚未加载）
    if (!guideCategories.value.length) {
      await loadGuideCategories()
    }
    ElMessage.success('速查指引推荐分析已生成')
  } catch (e) {
    ElMessage.error('生成失败')
  } finally {
    analysisLoading.top_questions_guide = false
  }
}

// 加载指引分类列表
async function loadGuideCategories() {
  try {
    const res = await getGuideCategories()
    guideCategories.value = res.data || []
  } catch (e) {
    // 静默失败
  }
}

// 全选/取消全选
function toggleAllRecommendations() {
  const newVal = !allRecommendationsSelected.value
  guideRecommendations.value.forEach(r => { r.enabled = newVal })
}

// 批量导入指引
async function handleBatchImport() {
  const items = enabledRecommendations.value
  if (!items.length) {
    ElMessage.warning('没有可导入的条目')
    return
  }
  // 校验分类
  const missing = items.filter(r => !r.category_id)
  if (missing.length) {
    ElMessage.warning(`有 ${missing.length} 条未选择目标分类，请先选择分类`)
    return
  }
  importLoading.value = true
  try {
    const payload = items.map(r => ({
      category_id: r.category_id,
      question: r.question.trim(),
      answer: r.suggested_answer.trim(),
    }))
    const res = await batchImportGuideItems(payload)
    const created = res.data?.created || 0
    const skipped = res.data?.skipped || []
    if (created > 0) {
      ElMessage.success(`成功导入 ${created} 条指引`)
    }
    if (skipped.length) {
      ElMessage.warning(`${skipped.length} 条导入失败：${skipped.map(s => s.reason).join('、')}`)
    }
    // 移除已成功导入的条目
    const importedKeys = new Set(payload.map(p => p.question))
    guideRecommendations.value = guideRecommendations.value.filter(r => !importedKeys.has(r.question.trim()))
  } catch (e) {
    ElMessage.error('导入失败')
  } finally {
    importLoading.value = false
  }
}

// 加载工单类型分布（按部门筛选）
async function loadTicketByTypeByDept() {
  await nextTick()
  const el = ticketByTypeByDeptChart.value
  if (!el) return
  if (chartInstances.type_by_dept) {
    chartInstances.type_by_dept.dispose()
  }
  const chart = echarts.init(el)
  chartInstances.type_by_dept = chart

  try {
    const res = await getTicketByTypeByDept(selectedDeptForType.value)
    const data = res.data?.data || []
    chart.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { bottom: 0, type: 'scroll' },
      series: [{
        type: 'pie', radius: ['40%', '70%'],
        label: { show: true, formatter: '{b}: {c}' },
        data: data.map(d => ({ name: d.name, value: d.value })),
      }],
    })
  } catch (e) {
    chart.setOption({ title: { text: '暂无数据', left: 'center', top: 'middle', textStyle: { color: '#9CA3AF', fontSize: 14 } } })
  }
}

// 加载工单部门分布（按类型筛选）
async function loadTicketByDeptByType() {
  await nextTick()
  const el = ticketByDeptByTypeChart.value
  if (!el) return
  if (chartInstances.dept_by_type) {
    chartInstances.dept_by_type.dispose()
  }
  const chart = echarts.init(el)
  chartInstances.dept_by_type = chart

  try {
    const res = await getTicketByDeptByType(selectedTypeForDept.value)
    const data = res.data?.data || []
    const items = data.slice().sort((a, b) => a.value - b.value)
    chart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 8, right: 24, top: 8, bottom: 8, containLabel: true },
      xAxis: { type: 'value', minInterval: 1 },
      yAxis: { type: 'category', data: items.map(i => i.name) },
      series: [{ type: 'bar', data: items.map(i => i.value), itemStyle: { color: '#3B82F6' }, barMaxWidth: 22 }],
    })
  } catch (e) {
    chart.setOption({ title: { text: '暂无数据', left: 'center', top: 'middle', textStyle: { color: '#9CA3AF', fontSize: 14 } } })
  }
}

// 加载工单状态分布
async function loadTicketStatus() {
  await nextTick()
  const el = ticketStatusChart.value
  if (!el) return
  if (chartInstances.ticket_status) {
    chartInstances.ticket_status.dispose()
  }
  const chart = echarts.init(el)
  chartInstances.ticket_status = chart

  try {
    const res = await getChartData('ticket_status')
    const data = res.data?.data || []
    chart.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { bottom: 0, type: 'scroll' },
      series: [{
        type: 'pie', radius: ['40%', '70%'],
        label: { show: true, formatter: '{b}: {c}' },
        data: data.map(d => ({ name: d.name, value: d.value })),
      }],
    })
  } catch (e) {
    chart.setOption({ title: { text: '暂无数据', left: 'center', top: 'middle', textStyle: { color: '#9CA3AF', fontSize: 14 } } })
  }
}

// AI分析处理函数
async function handleTicketByTypeAnalysis() {
  analysisLoading.type_by_dept = true
  try {
    const res = await generateTicketByTypeByDeptAnalysis(selectedDeptForType.value)
    analyses.type_by_dept = res.data?.content || ''
    ElMessage.success('AI 分析已生成')
  } catch (e) {
    ElMessage.error('生成失败')
  } finally {
    analysisLoading.type_by_dept = false
  }
}

async function handleTicketByDeptAnalysis() {
  analysisLoading.dept_by_type = true
  try {
    const res = await generateTicketByDeptByTypeAnalysis(selectedTypeForDept.value)
    analyses.dept_by_type = res.data?.content || ''
    ElMessage.success('AI 分析已生成')
  } catch (e) {
    ElMessage.error('生成失败')
  } finally {
    analysisLoading.dept_by_type = false
  }
}

async function handleTicketStatusAnalysis() {
  analysisLoading.ticket_status = true
  try {
    const res = await generateChartAnalysis('ticket_status')
    analyses.ticket_status = res.data?.content || ''
    ElMessage.success('AI 分析已生成')
  } catch (e) {
    ElMessage.error('生成失败')
  } finally {
    analysisLoading.ticket_status = false
  }
}

// 加载ROI数据
async function loadRoiData() {
  try {
    const res = await getRoiReport()
    roiReport.value = res.data || {}
  } catch (e) {}

  await nextTick()
  if (roiChartRef.value) {
    const chart = echarts.init(roiChartRef.value)
    const trend = roiReport.value.qa_trend || []
    chart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: trend.map(t => t.date) },
      yAxis: { type: 'value', name: '问答量' },
      series: [{ data: trend.map(t => t.count), type: 'bar', itemStyle: { color: '#D97706' } }]
    })
    chartInstances.roi = chart
  }
}

async function initTabCharts() {
  if (activeTab.value === 'overview') {
    await renderQaTrend()
    await renderCategoryDist()
    await renderTopQuestions()
  } else if (activeTab.value === 'tickets') {
    await loadTicketByTypeByDept()
    await loadTicketByDeptByType()
    await loadTicketStatus()
  } else if (activeTab.value === 'roi') {
    await loadRoiData()
  }
}

function handleResize() {
  Object.values(chartInstances).forEach(c => c?.resize())
}

watch(activeTab, async () => {
  await nextTick()
  await initTabCharts()
})

onMounted(async () => {
  window.addEventListener('resize', handleResize)

  // 加载部门列表
  try {
    const res = await getDepartments()
    departments.value = res.data || []
  } catch (e) {}

  await initTabCharts()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  Object.values(chartInstances).forEach(c => c?.dispose())
})
</script>

<style scoped>
.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.filter-group {
  display: flex;
  gap: 8px;
  align-items: center;
}
</style>
