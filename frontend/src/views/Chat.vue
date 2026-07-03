<template>
  <div class="chat-layout">
    <!-- 左侧对话列表 (桌面端) -->
    <div v-if="!isMobile" class="chat-sidebar">
      <el-button type="primary" class="new-chat-btn" @click="startNewChat">
        <el-icon><Plus /></el-icon>新建对话
      </el-button>
      <div class="conversation-list">
        <div v-for="group in chatStore.groups" :key="group.label" class="conv-group">
          <div class="conv-group-label">{{ dateGroupLabel(group.label) }}</div>
          <div v-for="conv in group.conversations" :key="conv.conversation_id"
               :class="['conv-item', { active: chatStore.currentConversationId === conv.conversation_id }]"
               @click="openConversation(conv.conversation_id)">
            <div class="conv-title">{{ conv.title }}</div>
            <el-button class="conv-delete" type="danger" :icon="Delete" circle size="small"
                       @click.stop="handleDeleteConv(conv.conversation_id)" />
          </div>
        </div>
        <div v-if="chatStore.groups.length === 0" class="empty-hint">暂无对话记录</div>
      </div>
    </div>

    <!-- 移动端对话列表抽屉 -->
    <el-drawer v-model="showMobileSidebar" direction="ltr" :size="280" :show-close="false" :with-header="false" class="chat-sidebar-drawer">
      <div style="padding: 12px">
        <el-button type="primary" style="width: 100%" @click="startNewChat(); showMobileSidebar = false">
          <el-icon><Plus /></el-icon>新建对话
        </el-button>
      </div>
      <div class="conversation-list">
        <div v-for="group in chatStore.groups" :key="group.label" class="conv-group">
          <div class="conv-group-label">{{ dateGroupLabel(group.label) }}</div>
          <div v-for="conv in group.conversations" :key="conv.conversation_id"
               :class="['conv-item', { active: chatStore.currentConversationId === conv.conversation_id }]"
               @click="openConversation(conv.conversation_id); showMobileSidebar = false">
            <div class="conv-title">{{ conv.title }}</div>
            <el-button class="conv-delete" type="danger" :icon="Delete" circle size="small"
                       @click.stop="handleDeleteConv(conv.conversation_id)" />
          </div>
        </div>
        <div v-if="chatStore.groups.length === 0" class="empty-hint">暂无对话记录</div>
      </div>
    </el-drawer>

    <!-- 移动端笔记抽屉 -->
    <el-drawer v-model="showMobileNotes" direction="rtl" :size="280" title="📝 我的笔记" class="chat-notes-drawer">
      <el-input v-model="notes" type="textarea" :autosize="false" placeholder="在这里记录笔记...&#10;&#10;可以记录对话要点、待办事项等" class="notes-textarea" />
    </el-drawer>

    <!-- 中间聊天区域 -->
    <div class="chat-main">
      <!-- 移动端工具栏 -->
      <div v-if="isMobile" class="mobile-chat-toolbar">
        <el-button text @click="showMobileSidebar = true">
          <el-icon :size="20"><Expand /></el-icon>
        </el-button>
        <span class="mobile-chat-title">HR 智能助手</span>
        <el-button text @click="showMobileNotes = true">
          <el-icon :size="20"><EditPen /></el-icon>
        </el-button>
      </div>

      <div class="chat-messages" ref="messagesRef">
        <!-- 欢迎屏 -->
        <div class="welcome" v-if="chatStore.messages.length === 0">
          <el-icon :size="isMobile ? 44 : 60" color="#D97706"><ChatDotRound /></el-icon>
          <h2>HR 智能助手</h2>
          <p>我可以帮你查询公司制度，也可以在需要办理事项时，引导你补全信息并生成工单，确认后提交给 HR。<br>你可以直接提问，例如"年假怎么计算"，也可以说"我想申请开具在职证明"。</p>

          <!-- 能力卡片 -->
          <div class="capability-cards">
            <div :class="['cap-card', { active: activeMode === 'policy' }]" @click="setMode('policy')">
              <div class="cap-card-header">
                <el-icon :size="24" color="#D97706"><Document /></el-icon>
                <span class="cap-card-title">查制度</span>
                <el-icon v-if="activeMode === 'policy'" class="cap-check" color="#D97706"><Select /></el-icon>
              </div>
              <div class="cap-card-desc">年假、请假、考勤、薪酬、福利等制度问题</div>
              <div class="cap-card-example">示例：工作满3年有几天年假？</div>
            </div>
            <div :class="['cap-card', { active: activeMode === 'service' }]" @click="setMode('service')">
              <div class="cap-card-header">
                <el-icon :size="24" color="#D97706"><Tickets /></el-icon>
                <span class="cap-card-title">办事项</span>
                <el-icon v-if="activeMode === 'service'" class="cap-check" color="#D97706"><Select /></el-icon>
              </div>
              <div class="cap-card-desc">证明开具、信息变更、人工处理等 HR 请求</div>
              <div class="cap-card-example">示例：我想申请开具在职证明</div>
            </div>
          </div>

          <!-- 推荐问题 -->
          <div class="quick-section">
            <div class="quick-title">你可以这样问</div>
            <div class="quick-questions">
              <el-tag v-for="q in currentQuestions" :key="q" effect="plain" style="cursor: pointer; margin: 4px" @click="sendQuick(q)">{{ q }}</el-tag>
            </div>
          </div>
        </div>

        <!-- 消息列表 -->
        <div v-for="(msg, idx) in chatStore.messages" :key="idx" :class="['message', msg.role]">
          <el-avatar v-if="msg.role === 'user'" :size="isMobile ? 30 : 36" style="background: #D97706; color: #fff">{{ userStore.userInfo.real_name?.[0] || 'U' }}</el-avatar>
          <el-avatar v-else :size="isMobile ? 30 : 36" style="background: #D97706; color: #fff"><ChatDotRound /></el-avatar>
          <div class="message-content">
            <div class="message-bubble" :class="msg.role">
              <!-- 工单确认卡片 -->
              <div v-if="msg.answer_type === 'ticket_confirm' && msg.ticket_draft" class="ticket-confirm-card">
                <div class="ticket-confirm-title">请确认以下工单信息：</div>
                <div class="ticket-confirm-row">
                  <span class="ticket-confirm-label">工单类型：</span>
                  <span class="ticket-confirm-value">{{ msg.ticket_draft.title || '' }}</span>
                </div>
                <div v-for="(value, key) in msg.ticket_draft.fields" :key="key" class="ticket-confirm-row">
                  <span class="ticket-confirm-label">{{ slotLabel(key) }}：</span>
                  <span class="ticket-confirm-value">{{ value === true ? '是' : value === false ? '否' : value }}</span>
                </div>
                <div class="ticket-confirm-actions">
                  <el-button type="primary" size="small" @click="confirmTicketSubmit(msg)">确认提交</el-button>
                  <el-button size="small" @click="modifyTicket(msg)">继续修改</el-button>
                </div>
              </div>
              <!-- 普通消息 -->
              <div v-else v-html="formatMessage(msg.content)"></div>
            </div>
            <!-- 回答类型标签 -->
            <div v-if="msg.role === 'assistant' && msg.answer_type" class="answer-type-tag">
              <el-tag v-if="msg.answer_type === 'faq'" type="success" size="small" effect="plain">标准答案</el-tag>
              <el-tag v-else-if="msg.answer_type === 'rule'" type="warning" size="small" effect="plain">规则答案</el-tag>
              <el-tag v-else-if="msg.answer_type === 'rag'" type="primary" size="small" effect="plain">已查阅制度文档</el-tag>
              <el-tag v-else-if="msg.answer_type === 'clarification'" type="info" size="small" effect="plain">需要补充信息</el-tag>
              <el-tag v-else-if="msg.answer_type === 'ticket_clarification'" type="warning" size="small" effect="plain">工单申请</el-tag>
              <el-tag v-else-if="msg.answer_type === 'ticket_confirm'" type="warning" size="small" effect="plain">待确认工单</el-tag>
              <el-tag v-else-if="msg.answer_type === 'ticket_submitted'" type="success" size="small" effect="plain">工单已提交</el-tag>
              <el-tag v-else-if="msg.answer_type === 'notice_confirm'" type="info" size="small" effect="plain">待确认</el-tag>
              <el-tag v-else-if="msg.answer_type === 'notice_form'" type="primary" size="small" effect="plain">发布公告</el-tag>
              <el-tag v-else-if="msg.answer_type === 'notice_published'" type="success" size="small" effect="plain">公告已发布</el-tag>
              <el-tag v-else-if="msg.answer_type === 'no_permission'" type="danger" size="small" effect="plain">无权限</el-tag>
              <el-tag v-else-if="msg.answer_type === 'miss'" type="info" size="small" effect="plain">未找到明确依据</el-tag>
              <el-tag v-else size="small" effect="plain">{{ msg.answer_type }}</el-tag>
            </div>
            <!-- 引用来源 -->
            <div v-if="msg.role === 'assistant' && msg.source_docs?.length" class="source-docs">
              <el-divider content-position="left"><span style="font-size: 12px; color: #9CA3AF">引用来源</span></el-divider>
              <el-tag v-for="(doc, i) in msg.source_docs" :key="i" size="small" type="info" style="margin: 2px">{{ docTitle(doc) }}</el-tag>
            </div>
            <!-- 未命中：操作按钮 -->
            <div v-if="msg.role === 'assistant' && msg.answer_type === 'miss'" class="miss-actions">
              <el-button size="small" @click="focusInput">继续补充问题</el-button>
              <el-button size="small" type="primary" @click="triggerTicketFlow('我需要 HR 人工处理问题')">转人工处理</el-button>
              <el-tag v-if="msg.miss_id" type="success" size="small" style="margin-left: 8px">已记录知识缺口</el-tag>
            </div>
            <!-- 操作按钮 -->
            <div v-if="msg.role === 'assistant' && msg.record_id && !['ticket_confirm', 'ticket_clarification'].includes(msg.answer_type)" class="message-actions">
              <el-button-group size="small">
                <el-button @click="feedback(msg, 'useful')" :type="msg.feedback === 'useful' ? 'success' : ''"><el-icon><Select /></el-icon></el-button>
                <el-button @click="feedback(msg, 'useless')" :type="msg.feedback === 'useless' ? 'danger' : ''"><el-icon><CloseBold /></el-icon></el-button>
              </el-button-group>
              <el-button size="small" @click="toggleFav(msg)" :type="msg.is_favorite ? 'warning' : ''">
                <el-icon><Star /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
        <!-- 加载动画 -->
        <div v-if="loading" class="message assistant">
          <el-avatar :size="isMobile ? 30 : 36" style="background: #D97706; color: #fff"><ChatDotRound /></el-avatar>
          <div class="message-content">
            <div class="message-bubble assistant loading-bubble">
              <span class="dot"></span><span class="dot"></span><span class="dot"></span>
            </div>
          </div>
        </div>
      </div>
      <div class="chat-input">
        <el-input v-model="input" :placeholder="inputPlaceholder" size="large" type="textarea" :autosize="{ minRows: 1, maxRows: 4 }" @keydown="handleKeydown" :disabled="loading" />
        <div style="display: flex; justify-content: flex-end; margin-top: 8px">
          <el-button type="primary" :icon="Promotion" @click="sendMessage" :loading="loading">发送</el-button>
        </div>
      </div>
    </div>

    <!-- 右侧笔记区 (桌面端) -->
    <div v-if="!isMobile" class="notes-panel">
      <div class="notes-header">
        <span style="font-weight: 600; color: #111827">📝 我的笔记</span>
      </div>
      <el-input v-model="notes" type="textarea" :autosize="false" placeholder="在这里记录笔记...&#10;&#10;可以记录对话要点、待办事项等" class="notes-textarea" />
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Promotion, ChatDotRound, Star, Select, CloseBold, Plus, Delete, Document, Tickets, Expand, EditPen } from '@element-plus/icons-vue'
import { sendChat, saveChatRecord } from '../api/chat'
import { createFeedback } from '../api/feedback'
import { toggleFavorite } from '../api/chatHistory'
import { useUserStore } from '../stores/user'
import { useChatStore } from '../stores/chat'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const chatStore = useChatStore()
const messagesRef = ref()
const input = ref('')
const loading = ref(false)
const notes = ref('')

// 移动端适配
const isMobile = ref(window.innerWidth <= 768)
const showMobileSidebar = ref(false)
const showMobileNotes = ref(false)

function handleResize() {
  isMobile.value = window.innerWidth <= 768
}

// ===== 能力模式 =====
const activeMode = ref('policy')

const policyQuestions = ref([
  '请假需要提前多久申请？',
  '年假怎么计算？',
  '工作满3年有几天年假？',
  '加班可以调休吗？',
  '试用期多久？',
  '绩效申诉怎么提交？',
])

const serviceQuestions = ref([
  '我想申请开具在职证明',
  '我要变更个人联系方式',
  '我想提交考勤异常说明',
  '我需要 HR 人工处理问题',
  '我要咨询证明材料需要什么',
  '我想申请补充薪资说明',
])

const currentQuestions = computed(() => activeMode.value === 'policy' ? policyQuestions.value : serviceQuestions.value)

const inputPlaceholder = computed(() =>
  activeMode.value === 'policy'
    ? '请输入你想查询的制度问题，例如"年假怎么计算？"'
    : '请输入你想办理的事项，例如"我想申请开具在职证明"'
)

function setMode(mode) {
  activeMode.value = mode
}

// ===== 笔记 =====
function notesKey(convId) { return convId ? `chat-notes-${convId}` : 'chat-notes-draft' }
function loadNotes(convId) { notes.value = localStorage.getItem(notesKey(convId)) || '' }
function saveNotes() { localStorage.setItem(notesKey(chatStore.currentConversationId), notes.value) }
watch(notes, saveNotes)

// ===== 工单引导（已迁移至后端） =====
// 工单意图识别、槽位提取、确认卡片均由后端处理
// 前端只负责渲染 ticket_clarification / ticket_confirm / ticket_submitted 标签

function triggerTicketFlow(question) {
  input.value = question
  sendMessage()
}

// ===== 公告引导（已下线，公告发布走HR后台页面） =====
// 聊天页不再处理公告发布，由后端返回提示引导用户到HR后台

// ===== 澄清追问（已禁用，由后端处理） =====
// 注意：澄清判断已移至后端 chat.py 处理
// 前端不再负责业务逻辑判断
function needsClarification(text) {
  return false
}

// ===== 消息渲染 =====
const dateGroupLabels = { today: '今天', yesterday: '昨天', last_7_days: '近7天', last_30_days: '近30天', earlier: '更早' }
function dateGroupLabel(label) { return dateGroupLabels[label] || label }

function formatMessage(text) {
  if (!text) return ''
  return text.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
}

function docTitle(doc) {
  return doc.title || doc.question || doc.name || doc.faq_id ? ('FAQ #' + doc.faq_id) : doc.rule_id ? ('规则 #' + doc.rule_id) : doc.doc_id ? ('文档 #' + doc.doc_id) : '来源文档'
}

// 工单槽位标签映射
function slotLabel(key) {
  const labels = {
    purpose: '证明用途',
    receiver: '接收单位',
    need_stamp: '是否需要盖章',
    expected_time: '期望完成时间',
    change_item: '变更信息类型',
    old_value: '原信息',
    new_value: '新信息',
    reason: '变更原因',
    exception_date: '异常日期',
    exception_type: '异常类型',
    description: '问题说明',
    issue_type: '问题类型'
  }
  return labels[key] || key
}

// 确认提交工单
async function confirmTicketSubmit(msg) {
  input.value = '确认提交'
  await sendMessage()
}

// 继续修改工单
async function modifyTicket(msg) {
  input.value = '继续修改'
  await sendMessage()
}

function focusInput() {
  nextTick(() => {
    const textarea = document.querySelector('.chat-input textarea')
    if (textarea) textarea.focus()
  })
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  })
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

function startNewChat() {
  chatStore.clearCurrentConversation()
  router.push('/chat')
}

function openConversation(convId) {
  router.push('/chat/' + convId)
}

async function handleDeleteConv(convId) {
  try {
    await ElMessageBox.confirm('确定删除该对话？', '提示', { type: 'warning' })
    await chatStore.removeConversation(convId)
    if (route.params.conversationId === convId) router.push('/chat')
    ElMessage.success('已删除')
  } catch {}
}

// ===== 知识缺口操作 =====
// 知识缺口已由后端自动记录，前端只展示按钮状态
// 用户点击"已记录"按钮时，不需要重复提交

// ===== 核心：发送消息 =====
async function sendMessage() {
  const q = input.value.trim()
  if (!q || loading.value) return
  input.value = ''
  chatStore.messages.push({ role: 'user', content: q })
  scrollToBottom()

  // 调用后端 API，让后端处理所有业务逻辑
  loading.value = true
  try {
    const res = await sendChat({ question: q, conversation_id: chatStore.currentConversationId })
    const data = res.data

    // 保存后端返回的 conversation_id
    if (data.conversation_id) {
      chatStore.currentConversationId = data.conversation_id
    }

    // 渲染后端返回的回答
    chatStore.messages.push({
      role: 'assistant',
      content: data.answer,
      answer_type: data.answer_type,
      intent: data.intent || null,
      source_docs: data.source_docs || [],
      required_slots: data.required_slots || [],
      filled_slots: data.filled_slots || {},
      actions: data.actions || [],
      ticket_draft: data.ticket_draft || null,
      ticket: data.ticket || null,
      miss_id: data.miss_id || null,
      record_id: data.record_id,
      feedback: null,
      is_favorite: false,
    })

    // 更新URL和会话列表
    const convId = data.conversation_id
    if (convId && route.params.conversationId !== convId) {
      const draftNotes = localStorage.getItem(notesKey(null)) || ''
      if (draftNotes && !localStorage.getItem(notesKey(convId))) {
        localStorage.setItem(notesKey(convId), draftNotes)
        localStorage.removeItem(notesKey(null))
      }
      router.replace('/chat/' + convId)
    }
    chatStore.fetchConversations()
  } catch (e) {
    chatStore.messages.push({ role: 'assistant', content: '抱歉，发生了错误，请稍后重试。' })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

function sendQuick(q) {
  input.value = q
  sendMessage()
}

// ===== 反馈 =====
async function feedback(msg, type) {
  try {
    await createFeedback({ record_id: msg.record_id, feedback_type: type })
    msg.feedback = type
    ElMessage.success(type === 'useful' ? '感谢反馈' : '已记录，我们会改进')
  } catch (e) {}
}

async function toggleFav(msg) {
  try {
    const res = await toggleFavorite(msg.record_id)
    msg.is_favorite = res.data.is_favorite
    ElMessage.success(msg.is_favorite ? '已收藏' : '已取消收藏')
  } catch (e) {}
}

// ===== 路由 =====
watch(() => route.params.conversationId, (newId) => {
  if (newId) chatStore.loadConversation(newId)
  else chatStore.clearCurrentConversation()
  loadNotes(newId)
})

onMounted(async () => {
  chatStore.fetchConversations()
  if (route.params.conversationId) {
    chatStore.loadConversation(route.params.conversationId)
    loadNotes(route.params.conversationId)
  } else {
    loadNotes(null)
  }
  if (route.query.q) {
    input.value = route.query.q
    sendMessage()
  }
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.chat-layout { display: flex; height: calc(100vh - 120px); background: #fff; border-radius: 12px; overflow: hidden; border: 1px solid #e5e7eb; }
.chat-sidebar { width: 260px; border-right: 1px solid #f3f4f6; display: flex; flex-direction: column; flex-shrink: 0; background: #fafafa; }
.new-chat-btn { margin: 12px; }
.conversation-list { flex: 1; overflow-y: auto; padding: 0 8px 12px; }
.conv-group-label { padding: 8px 12px 4px; font-size: 12px; color: #9CA3AF; font-weight: 600; }
.conv-item { display: flex; align-items: center; padding: 10px 12px; border-radius: 8px; cursor: pointer; margin-bottom: 2px; transition: background 0.15s; }
.conv-item:hover { background: #f3f4f6; }
.conv-item.active { background: #FFF7ED; }
.conv-item.active .conv-title { color: #D97706; font-weight: 500; }
.conv-title { flex: 1; font-size: 14px; color: #374151; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.conv-delete { opacity: 0; transition: opacity 0.15s; flex-shrink: 0; }
.conv-item:hover .conv-delete { opacity: 1; }
.empty-hint { text-align: center; color: #9CA3AF; padding: 40px 20px; font-size: 14px; }
.chat-main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.chat-messages { flex: 1; overflow-y: auto; padding: 24px; }

/* 欢迎屏 */
.welcome { text-align: center; padding: 48px 20px 24px; }
.welcome h2 { margin: 16px 0 8px; color: #111827; font-weight: 700; font-size: 24px; letter-spacing: -0.3px; }
.welcome p { color: #6B7280; margin-bottom: 28px; font-size: 14px; line-height: 1.8; max-width: 520px; margin-left: auto; margin-right: auto; }

/* 能力卡片 */
.capability-cards { display: flex; gap: 16px; justify-content: center; margin-bottom: 28px; max-width: 520px; margin-left: auto; margin-right: auto; }
.cap-card { flex: 1; padding: 20px; border: 2px solid #e5e7eb; border-radius: 12px; cursor: pointer; text-align: left; transition: all 0.2s; background: #fff; }
.cap-card:hover { border-color: #fbbf24; }
.cap-card.active { border-color: #D97706; background: #FFF7ED; }
.cap-card-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.cap-card-title { font-size: 16px; font-weight: 600; color: #111827; }
.cap-check { margin-left: auto; }
.cap-card-desc { font-size: 13px; color: #6B7280; margin-bottom: 8px; }
.cap-card-example { font-size: 12px; color: #9CA3AF; font-style: italic; }

/* 推荐问题 */
.quick-section { max-width: 520px; margin: 0 auto; }
.quick-title { font-size: 13px; color: #9CA3AF; margin-bottom: 10px; }
.quick-questions { display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; }

/* 消息 */
.message { display: flex; gap: 12px; margin-bottom: 24px; }
.message.user { flex-direction: row-reverse; }
.message-content { max-width: 70%; }
.message-bubble { padding: 14px 18px; border-radius: 16px; line-height: 1.7; font-size: 14px; }
.message-bubble.user { background: #D97706; color: #fff; border-top-right-radius: 4px; }
.message-bubble.assistant { background: #f9fafb; color: #111827; border-top-left-radius: 4px; border: 1px solid #f3f4f6; }
.message-actions { margin-top: 8px; display: flex; gap: 8px; }
.answer-type-tag { margin-top: 6px; }
.source-docs { margin-top: 8px; }
.miss-actions { margin-top: 10px; display: flex; gap: 8px; }

/* 工单确认卡片 */
.ticket-confirm-card { font-size: 14px; }
.ticket-confirm-title { font-weight: 600; margin-bottom: 12px; color: #111827; }
.ticket-confirm-row { margin-bottom: 8px; line-height: 1.6; }
.ticket-confirm-label { color: #6B7280; }
.ticket-confirm-value { color: #111827; font-weight: 500; }
.ticket-confirm-actions { margin-top: 16px; display: flex; gap: 8px; }

/* 加载动画 */
.loading-bubble { display: flex; gap: 6px; align-items: center; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: #D97706; opacity: 0.4; animation: bounce 1.4s infinite ease-in-out both; }
.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }
@keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }

/* 输入框 */
.chat-input { padding: 16px 20px; border-top: 1px solid #f3f4f6; }

/* 笔记区 */
.notes-panel { width: 280px; border-left: 1px solid #f3f4f6; display: flex; flex-direction: column; background: #fafafa; flex-shrink: 0; }
.notes-header { padding: 16px; border-bottom: 1px solid #f3f4f6; }
.notes-textarea { flex: 1; }
.notes-textarea :deep(.el-textarea__inner) { height: 100% !important; border: none; border-radius: 0; resize: none; background: transparent; box-shadow: none; padding: 16px; font-size: 13px; line-height: 1.8; }

/* 移动端工具栏 */
.mobile-chat-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  border-bottom: 1px solid #f3f4f6;
  background: #fff;
  flex-shrink: 0;
}
.mobile-chat-title {
  font-size: 15px;
  font-weight: 600;
  color: #111827;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .chat-layout {
    border-radius: 0;
    border: none;
    height: calc(100vh - 108px);
  }
  .chat-messages {
    padding: 12px;
  }
  .capability-cards {
    flex-direction: column;
    gap: 12px;
  }
  .cap-card {
    padding: 14px;
  }
  .welcome {
    padding: 24px 12px 16px;
  }
  .welcome h2 {
    font-size: 20px;
  }
  .welcome p {
    font-size: 13px;
    margin-bottom: 20px;
  }
  .message-content {
    max-width: 85%;
  }
  .message-bubble {
    padding: 10px 14px;
    font-size: 13px;
  }
  .miss-actions {
    flex-wrap: wrap;
    gap: 6px;
  }
  .message-actions {
    flex-wrap: wrap;
  }
  .chat-input {
    padding: 10px 12px;
  }
  .quick-questions {
    gap: 6px;
  }
  .quick-questions .el-tag {
    font-size: 12px;
  }
}

/* 移动端抽屉样式 */
:deep(.chat-sidebar-drawer .el-drawer__body) {
  padding: 0;
  overflow: hidden;
}
:deep(.chat-notes-drawer .el-drawer__body) {
  padding: 0;
  display: flex;
  flex-direction: column;
}

@media (max-width: 768px) {
  :deep(.chat-notes-drawer) {
    width: 88vw !important;
  }
}
</style>
