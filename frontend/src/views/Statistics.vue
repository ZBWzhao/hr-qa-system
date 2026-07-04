<template>
  <div>
    <el-row :gutter="20">
      <el-col :xs="24" :sm="24" :md="12">
        <el-card>
          <template #header><span style="font-weight: 600; color: #111827">问答量趋势</span></template>
          <div ref="trendChart" style="height: 350px"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="24" :md="12">
        <el-card>
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span style="font-weight: 600; color: #111827">咨询类别分布</span>
              <el-button text type="primary" size="small" @click="$router.push('/todo')">查看详情</el-button>
            </div>
          </template>
          <div ref="categoryChart" style="height: 350px"></div>
        </el-card>
      </el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :xs="24" :sm="24" :md="12">
        <el-card>
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span style="font-weight: 600; color: #111827">高频问题排行</span>
              <el-button text type="primary" size="small" @click="$router.push('/history')">查看详情</el-button>
            </div>
          </template>
          <div ref="faqChart" style="height: 350px"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="24" :md="12">
        <el-card>
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span style="font-weight: 600; color: #111827">工单状态分布</span>
              <el-button text type="primary" size="small" @click="$router.push('/todo')">查看详情</el-button>
            </div>
          </template>
          <div ref="ticketChart" style="height: 350px"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { getRoiReport } from '../api/roi'
import { getTicketStats } from '../api/tickets'
import { getTopQuestions, getCategoryStats } from '../api/chat'

const router = useRouter()

const trendChart = ref()
const categoryChart = ref()
const faqChart = ref()
const ticketChart = ref()
const charts = []

function handleResize() {
  charts.forEach(c => c?.resize())
}

onMounted(async () => {
  await nextTick()
  initTrendChart()
  initCategoryChart()
  initFaqChart()
  initTicketChart()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  charts.forEach(c => c?.dispose())
})

async function initTrendChart() {
  const chart = echarts.init(trendChart.value)
  charts.push(chart)
  try {
    const res = await getRoiReport()
    const trend = res.data?.qa_trend || []
    chart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: trend.map(t => t.date) },
      yAxis: { type: 'value' },
      series: [{ data: trend.map(t => t.count), type: 'line', smooth: true, areaStyle: { opacity: 0.3 }, itemStyle: { color: '#D97706' } }]
    })
  } catch (e) {
    chart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: ['1月', '2月', '3月', '4月', '5月', '6月'] },
      yAxis: { type: 'value' },
      series: [{ data: [120, 200, 150, 80, 70, 110], type: 'line', smooth: true, areaStyle: { opacity: 0.3 }, itemStyle: { color: '#D97706' } }]
    })
  }
}

async function initCategoryChart() {
  const chart = echarts.init(categoryChart.value)
  charts.push(chart)
  try {
    const res = await getCategoryStats()
    const categories = res.data || []
    chart.setOption({
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} ({d}%)'
      },
      legend: {
        bottom: 0,
        type: 'scroll'
      },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        label: {
          show: true,
          formatter: '{b}: {c}'
        },
        data: categories.map(c => ({
          value: c.value,
          name: c.name,
          type: c.type
        }))
      }]
    })

    // 添加点击事件
    chart.on('click', function(params) {
      router.push('/todo')
    })
  } catch (e) {
    // 如果获取失败，显示默认数据
    chart.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: 0 },
      series: [{
        type: 'pie', radius: ['40%', '70%'],
        data: [
          { value: 0, name: '暂无数据' }
        ]
      }]
    })
  }
}

async function initFaqChart() {
  const chart = echarts.init(faqChart.value)
  charts.push(chart)
  const truncateText = (text, maxLen = 16) => {
    if (!text) return ''
    return text.length > maxLen ? text.substring(0, maxLen) + '…' : text
  }
  try {
    const res = await getTopQuestions({ limit: 8 })
    const items = (res.data || []).slice().sort((a, b) => a.count - b.count)
    if (!items.length) {
      chart.setOption({
        title: { text: '暂无问答数据', left: 'center', top: 'middle', textStyle: { color: '#9CA3AF', fontSize: 14 } },
        xAxis: { show: false },
        yAxis: { show: false },
        series: [],
      })
      return
    }
    const chartHeight = Math.max(320, items.length * 38 + 40)
    faqChart.value.style.height = `${chartHeight}px`
    chart.resize()
    chart.setOption({
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter(params) {
          const p = params[0]
          const item = items[p.dataIndex]
          return `${item?.question || ''}<br/>提问次数：${p.value}`
        },
      },
      grid: { left: 8, right: 24, top: 8, bottom: 8, containLabel: true },
      xAxis: {
        type: 'value',
        minInterval: 1,
        splitLine: { lineStyle: { type: 'dashed', color: '#eee' } },
      },
      yAxis: {
        type: 'category',
        data: items.map(i => truncateText(i.question)),
        axisLabel: { fontSize: 11, width: 110, overflow: 'truncate' },
      },
      series: [{
        type: 'bar',
        data: items.map(i => i.count),
        itemStyle: { color: '#059669' },
        barMaxWidth: 22,
      }],
    })
    chart.on('click', () => router.push('/history'))
  } catch (e) {
    chart.setOption({
      title: { text: '加载失败', left: 'center', top: 'middle', textStyle: { color: '#9CA3AF', fontSize: 14 } },
      series: [],
    })
  }
}

async function initTicketChart() {
  const chart = echarts.init(ticketChart.value)
  charts.push(chart)
  try {
    const res = await getTicketStats()
    const d = res.data || {}
    chart.setOption({
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} ({d}%)'
      },
      legend: { bottom: 0 },
      series: [{
        type: 'pie', radius: ['40%', '70%'],
        label: {
          show: true,
          formatter: '{b}: {c}'
        },
        data: [
          { value: d.pending || 0, name: '待处理' },
          { value: d.processing || 0, name: '处理中' },
          { value: d.completed || 0, name: '已完成' },
          { value: d.rejected || 0, name: '已驳回' }
        ]
      }]
    })

    // 添加点击事件
    chart.on('click', function(params) {
      router.push('/todo')
    })
  } catch (e) {}
}
</script>
