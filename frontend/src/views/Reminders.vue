<template>
  <el-card>
    <template #header><span style="font-weight: 600; color: #111827">到期提醒</span></template>
    <div v-for="(r, idx) in reminders" :key="idx" class="reminder-item">
      <el-icon :size="20" :color="r.urgent ? '#DC2626' : '#D97706'" style="margin-right: 12px"><AlarmClock /></el-icon>
      <div style="flex: 1">
        <div>{{ r.message }}</div>
        <div style="color: #9CA3AF; font-size: 12px; margin-top: 4px">类型：{{ typeLabel(r.type) }} | 日期：{{ r.date }}</div>
      </div>
      <el-tag v-if="r.urgent" type="danger" size="small">紧急</el-tag>
    </div>
    <el-empty v-if="!reminders.length" description="暂无提醒" />

    <template v-if="userStore.isHR">
      <el-divider />
      <h4 style="margin-bottom: 16px">提醒规则配置</h4>
      <el-button type="primary" size="small" style="margin-bottom: 12px" @click="showRuleDialog()">新增规则</el-button>
      <el-table :data="rules" stripe size="small">
        <el-table-column prop="name" label="规则名称" />
        <el-table-column prop="rule_type" label="类型" width="120" />
        <el-table-column prop="trigger_days" label="提前天数" width="100" />
        <el-table-column prop="channels" label="通知渠道" width="120" />
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }"><el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '启用' : '禁用' }}</el-tag></template>
        </el-table-column>
      </el-table>
    </template>

    <el-dialog v-model="ruleDialogVisible" title="新增提醒规则" width="500px">
      <el-form :model="ruleForm" label-width="80px">
        <el-form-item label="名称"><el-input v-model="ruleForm.name" /></el-form-item>
        <el-form-item label="类型">
          <el-select v-model="ruleForm.rule_type">
            <el-option label="合同到期" value="contract" />
            <el-option label="试用期" value="probation" />
            <el-option label="年假" value="annual_leave" />
          </el-select>
        </el-form-item>
        <el-form-item label="提前天数"><el-input-number v-model="ruleForm.trigger_days" :min="1" /></el-form-item>
        <el-form-item label="模板"><el-input v-model="ruleForm.template" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="ruleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitRule">确定</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getReminders, getReminderRules, createReminderRule } from '../api/reminders'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const reminders = ref([])
const rules = ref([])
const ruleDialogVisible = ref(false)
const ruleForm = reactive({ name: '', rule_type: 'contract', trigger_days: 30, template: '' })

function typeLabel(t) { return { contract: '合同到期', probation: '试用期', annual_leave: '年假', training: '培训' }[t] || t }

async function fetchData() {
  try { const res = await getReminders(); reminders.value = res.data || [] } catch (e) {}
  if (userStore.isHR) {
    try { const res = await getReminderRules(); rules.value = res.data || [] } catch (e) {}
  }
}

function showRuleDialog() { Object.assign(ruleForm, { name: '', rule_type: 'contract', trigger_days: 30, template: '' }); ruleDialogVisible.value = true }

async function submitRule() {
  await createReminderRule(ruleForm)
  ElMessage.success('创建成功')
  ruleDialogVisible.value = false
  fetchData()
}

onMounted(() => fetchData())
</script>

<style scoped>
.reminder-item { display: flex; align-items: flex-start; padding: 16px; border: 1px solid #f3f4f6; border-radius: 12px; margin-bottom: 12px; }
</style>