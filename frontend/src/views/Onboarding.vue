<template>
  <el-card>
    <template #header><span style="font-weight: 700">入职引导</span></template>
    <el-alert v-if="data.is_new_employee" title="欢迎加入公司！以下是您的入职学习清单，请认真阅读相关制度文档。" type="success" :closable="false" style="margin-bottom: 20px" />
    <el-alert v-else title="您已完成入职引导期，以下为公司制度文档，可随时查阅。" type="info" :closable="false" style="margin-bottom: 20px" />

    <h4 style="margin-bottom: 16px">制度文档学习清单</h4>
    <el-table :data="data.checklist" stripe>
      <el-table-column prop="title" label="文档名称" min-width="300" />
      <el-table-column prop="category" label="分类" width="120" />
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="markRead(row)">标记已读</el-button>
        </template>
      </el-table-column>
    </el-table>

    <h4 style="margin: 24px 0 16px">常见入职问题</h4>
    <div v-for="(faq, idx) in data.faqs" :key="idx" style="padding: 12px 0; border-bottom: 1px solid #f0f0f0">
      <div style="font-weight: 500; color: #333">{{ faq.question }}</div>
      <div style="color: #999; font-size: 12px; margin-top: 4px">分类：{{ faq.category }}</div>
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getOnboarding, markDocRead } from '../api/onboarding'

const data = ref({ is_new_employee: false, checklist: [], faqs: [], progress: 0 })

async function fetchData() {
  try {
    const res = await getOnboarding()
    data.value = res.data || data.value
  } catch (e) {}
}

async function markRead(row) {
  await markDocRead(row.id)
  ElMessage.success('已标记为已读')
}

onMounted(() => fetchData())
</script>