<template>
  <div>
    <el-row :gutter="20" style="margin-bottom: 20px">
      <el-col :span="6">
        <el-card shadow="hover"><el-statistic title="本月问答量" :value="report.month_qa || 0" /></el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover"><el-statistic title="本月节省工时(h)" :value="report.month_saved_hours || 0" /></el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover"><el-statistic title="等效全职HR" :value="report.equivalent_fte || 0" /></el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover"><el-statistic title="ROI百分比" :value="report.roi_percentage || 0" suffix="%" /></el-card>
      </el-col>
    </el-row>
    <el-card>
      <template #header><span style="font-weight: 600; color: #111827">ROI分析报告</span></template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="总问答量">{{ report.total_qa }}</el-descriptions-item>
        <el-descriptions-item label="本月问答量">{{ report.month_qa }}</el-descriptions-item>
        <el-descriptions-item label="总工单量">{{ report.total_tickets }}</el-descriptions-item>
        <el-descriptions-item label="本月工单量">{{ report.month_tickets }}</el-descriptions-item>
        <el-descriptions-item label="总节省工时">{{ report.total_saved_hours }} 小时</el-descriptions-item>
        <el-descriptions-item label="本月节省工时">{{ report.month_saved_hours }} 小时</el-descriptions-item>
      </el-descriptions>
      <el-divider />
      <div style="padding: 16px; background: #ECFDF5; border-radius: 12px; color: #059669; font-size: 16px">{{ report.report_summary }}</div>
      <div ref="roiChart" style="height: 300px; margin-top: 20px"></div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getRoiReport } from '../api/roi'

const report = ref({})
const roiChart = ref()

onMounted(async () => {
  try {
    const res = await getRoiReport()
    report.value = res.data || {}
  } catch (e) {}

  await nextTick()
  const chart = echarts.init(roiChart.value)
  const trend = report.value.qa_trend || []
  chart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: trend.map(t => t.date) },
    yAxis: { type: 'value', name: '问答量' },
    series: [{ data: trend.map(t => t.count), type: 'bar', itemStyle: { color: '#D97706' } }]
  })
})
</script>
