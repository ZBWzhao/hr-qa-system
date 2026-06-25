<template>
  <div>
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header><span style="font-weight: 700">问答量趋势</span></template>
          <div ref="trendChart" style="height: 350px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header><span style="font-weight: 700">咨询类别分布</span></template>
          <div ref="categoryChart" style="height: 350px"></div>
        </el-card>
      </el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card>
          <template #header><span style="font-weight: 700">高频问题排行</span></template>
          <div ref="faqChart" style="height: 350px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header><span style="font-weight: 700">工单状态分布</span></template>
          <div ref="ticketChart" style="height: 350px"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getRoiReport } from '../api/roi'
import { getTicketStats } from '../api/tickets'
import { getFaqs } from '../api/faqs'

const trendChart = ref()
const categoryChart = ref()
const faqChart = ref()
const ticketChart = ref()

onMounted(async () => {
  await nextTick()
  initTrendChart()
  initCategoryChart()
  initFaqChart()
  initTicketChart()
})

async function initTrendChart() {
  const chart = echarts.init(trendChart.value)
  try {
    const res = await getRoiReport()
    const trend = res.data?.qa_trend || []
    chart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: trend.map(t => t.date) },
      yAxis: { type: 'value' },
      series: [{ data: trend.map(t => t.count), type: 'line', smooth: true, areaStyle: { opacity: 0.3 }, itemStyle: { color: '#1890ff' } }]
    })
  } catch (e) {
    chart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: ['1月', '2月', '3月', '4月', '5月', '6月'] },
      yAxis: { type: 'value' },
      series: [{ data: [120, 200, 150, 80, 70, 110], type: 'line', smooth: true, areaStyle: { opacity: 0.3 }, itemStyle: { color: '#1890ff' } }]
    })
  }
}

function initCategoryChart() {
  const chart = echarts.init(categoryChart.value)
  chart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie', radius: ['40%', '70%'],
      data: [
        { value: 35, name: '考勤' },
        { value: 25, name: '休假' },
        { value: 20, name: '薪酬' },
        { value: 15, name: '绩效' },
        { value: 5, name: '其他' }
      ]
    }]
  })
}

async function initFaqChart() {
  const chart = echarts.init(faqChart.value)
  try {
    const res = await getFaqs({ page_size: 10 })
    const faqs = res.data?.items || []
    chart.setOption({
      tooltip: {},
      xAxis: { type: 'value' },
      yAxis: { type: 'category', data: faqs.map(f => f.question.substring(0, 10) + '...').reverse() },
      series: [{ type: 'bar', data: faqs.map(f => f.view_count).reverse(), itemStyle: { color: '#52c41a' } }]
    })
  } catch (e) {
    chart.setOption({
      tooltip: {},
      xAxis: { type: 'value' },
      yAxis: { type: 'category', data: ['年假计算', '请假流程', '报销流程', '加班调休', '绩效申诉'] },
      series: [{ type: 'bar', data: [150, 120, 100, 80, 60], itemStyle: { color: '#52c41a' } }]
    })
  }
}

async function initTicketChart() {
  const chart = echarts.init(ticketChart.value)
  try {
    const res = await getTicketStats()
    const d = res.data || {}
    chart.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: 0 },
      series: [{
        type: 'pie', radius: ['40%', '70%'],
        data: [
          { value: d.pending || 0, name: '待处理' },
          { value: d.processing || 0, name: '处理中' },
          { value: d.completed || 0, name: '已完成' },
          { value: d.rejected || 0, name: '已驳回' }
        ]
      }]
    })
  } catch (e) {}
}
</script>
