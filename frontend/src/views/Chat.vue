<template>
  <div class="chat-layout">
    <!-- 左侧对话列表 -->
    <div class="chat-sidebar">
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

    <!-- 中间聊天区域 -->
    <div class="chat-main">
      <div class="chat-messages" ref="messagesRef">
        <!-- 欢迎屏 -->
        <div class="welcome" v-if="chatStore.messages.length === 0">
          <el-icon :size="60" color="#D97706"><ChatDotRound /></el-icon>
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
          <el-avatar v-if="msg.role === 'user'" :size="36" style="background: #D97706; color: #fff">{{ userStore.userInfo.real_name?.[0] || 'U' }}</el-avatar>
          <el-avatar v-else :size="36" style="background: #D97706; color: #fff"><ChatDotRound /></el-avatar>
          <div class="message-content">
            <div class="message-bubble" :class="msg.role">
              <div v-html="formatMessage(msg.content)"></div>
            </div>
            <!-- 回答类型标签 -->
            <div v-if="msg.role === 'assistant' && msg.answer_type" class="answer-type-tag">
              <el-tag v-if="msg.answer_type === 'faq'" type="success" size="small" effect="plain">标准答案</el-tag>
              <el-tag v-else-if="msg.answer_type === 'rule'" type="warning" size="small" effect="plain">规则答案</el-tag>
              <el-tag v-else-if="msg.answer_type === 'rag'" type="primary" size="small" effect="plain">已查阅制度文档</el-tag>
              <el-tag v-else-if="msg.answer_type === 'clarification'" type="info" size="small" effect="plain">需要补充信息</el-tag>
              <el-tag v-else-if="msg.answer_type === 'ticket_form'" type="warning" size="small" effect="plain">工单申请</el-tag>
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
            <!-- 未命中：转人工按钮 -->
            <div v-if="msg.role === 'assistant' && msg.answer_type === 'miss'" class="miss-actions">
              <el-button size="small" @click="focusInput">继续补充问题</el-button>
              <el-button size="small" type="primary" @click="triggerTicketFlow('我需要 HR 人工处理问题')">转人工处理</el-button>
            </div>
            <!-- 操作按钮 -->
            <div v-if="msg.role === 'assistant' && msg.record_id && !msg.ticket_confirm" class="message-actions">
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
          <el-avatar :size="36" style="background: #D97706; color: #fff"><ChatDotRound /></el-avatar>
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

    <!-- 右侧笔记区 -->
    <div class="notes-panel">
      <div class="notes-header">
        <span style="font-weight: 600; color: #111827">📝 我的笔记</span>
      </div>
      <el-input v-model="notes" type="textarea" :autosize="false" placeholder="在这里记录笔记...&#10;&#10;可以记录对话要点、待办事项等" class="notes-textarea" />
    </div>

    <!-- 工单表单对话框 -->
    <el-dialog v-model="ticketDialogVisible" title="提交人工请求" width="500px" :close-on-click-modal="false">
      <el-form :model="ticketForm" label-width="100px">
        <el-form-item label="请求类型">
          <el-select v-model="ticketForm.type" style="width: 100%">
            <el-option label="证明开具" value="certify" />
            <el-option label="信息变更" value="info_change" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题">
          <el-input v-model="ticketForm.title" placeholder="简要描述您的需求" />
        </el-form-item>
        <el-form-item label="具体原因">
          <el-input v-model="ticketForm.reason" type="textarea" :rows="3" placeholder="请说明具体原因或用途" />
        </el-form-item>
        <el-form-item label="期望完成时间">
          <el-input v-model="ticketForm.deadline" placeholder="例如：下周三之前" />
        </el-form-item>
        <el-form-item label="补充说明">
          <el-input v-model="ticketForm.description" type="textarea" :rows="3" placeholder="其他需要补充的信息（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="ticketDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitTicketForm" :loading="ticketSubmitting">提交</el-button>
      </template>
    </el-dialog>

    <!-- 公告表单对话框 -->
    <el-dialog v-model="noticeDialogVisible" title="发布公告" width="600px" :close-on-click-modal="false">
      <el-form :model="noticeForm" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="noticeForm.title" placeholder="请输入公告标题" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="noticeForm.content" type="textarea" :rows="6" placeholder="请输入公告内容" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="noticeForm.notice_type" style="width: 100%">
            <el-option label="一般" value="general" />
            <el-option label="政策" value="policy" />
            <el-option label="假期" value="holiday" />
            <el-option label="提醒" value="reminder" />
          </el-select>
        </el-form-item>
        <el-form-item label="置顶">
          <el-switch v-model="noticeForm.is_pinned" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="noticeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitNoticeForm" :loading="noticeSubmitting">发布</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Promotion, ChatDotRound, Star, Select, CloseBold, Plus, Delete, Document, Tickets } from '@element-plus/icons-vue'
import { sendChat, saveChatRecord } from '../api/chat'
import { createFeedback } from '../api/feedback'
import { toggleFavorite } from '../api/chatHistory'
import { createTicket } from '../api/tickets'
import { createNotice } from '../api/notices'
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

// ===== 工单引导 =====
const ticketKeywords = ['申请', '办理', '开具', '证明', '信息变更', '转人工', '联系HR', '提交工单', '人工处理', '考勤异常']
const ticketTypeMap = {
  '证明': 'certify', '在职': 'certify', '开具': 'certify',
  '变更': 'info_change', '修改': 'info_change', '联系方式': 'info_change',
  '考勤': 'other', '异常': 'other',
}

// 工单表单相关
const ticketDialogVisible = ref(false)
const ticketSubmitting = ref(false)
const ticketForm = reactive({
  type: 'other',
  title: '',
  reason: '',
  deadline: '',
  description: ''
})

function isTicketIntent(text) {
  return ticketKeywords.some(kw => text.includes(kw))
}

function guessTicketType(text) {
  for (const [kw, type] of Object.entries(ticketTypeMap)) {
    if (text.includes(kw)) return type
  }
  return 'other'
}

function triggerTicketFlow(question) {
  input.value = question
  sendMessage()
}

function openTicketDialog(type, title) {
  ticketForm.type = type
  ticketForm.title = title
  ticketForm.reason = ''
  ticketForm.deadline = ''
  ticketForm.description = ''
  ticketDialogVisible.value = true
}

// ===== 公告引导 =====
const noticeKeywords = [
  '发布公告', '发通知', '发布通知', '发公告', '通知公告',
  '通知大家', '通知全体员工', '发一个通知', '发一个公告',
  '写通知', '写公告', '公告', '通知'
]

// 公告表单相关
const noticeDialogVisible = ref(false)
const noticeSubmitting = ref(false)
const noticeForm = reactive({
  title: '',
  content: '',
  notice_type: 'general',
  is_pinned: 0
})

function isNoticeIntent(text) {
  // 检查是否包含公告相关关键词
  return noticeKeywords.some(kw => text.includes(kw))
}

function openNoticeDialog() {
  noticeForm.title = ''
  noticeForm.content = ''
  noticeForm.notice_type = 'general'
  noticeForm.is_pinned = 0
  noticeDialogVisible.value = true
}

async function submitNoticeForm() {
  if (!noticeForm.title.trim()) {
    ElMessage.warning('请填写公告标题')
    return
  }
  if (!noticeForm.content.trim()) {
    ElMessage.warning('请填写公告内容')
    return
  }

  noticeSubmitting.value = true
  try {
    await createNotice(noticeForm)
    noticeDialogVisible.value = false

    // 在聊天记录中添加发布成功的消息
    chatStore.messages.push({
      role: 'assistant',
      content: `公告已发布成功！\n\n标题：${noticeForm.title}`,
      answer_type: 'notice_published',
      source_docs: [],
      record_id: null,
      feedback: null,
      is_favorite: false,
    })
    scrollToBottom()
    ElMessage.success('公告发布成功')
  } catch (e) {
    ElMessage.error('发布失败，请稍后重试')
  } finally {
    noticeSubmitting.value = false
  }
}

async function submitTicketForm() {
  if (!ticketForm.title.trim()) {
    ElMessage.warning('请填写标题')
    return
  }
  if (!ticketForm.reason.trim()) {
    ElMessage.warning('请填写具体原因')
    return
  }

  ticketSubmitting.value = true
  try {
    // 构建描述信息
    let description = `原因：${ticketForm.reason}`
    if (ticketForm.deadline) description += `\n期望完成时间：${ticketForm.deadline}`
    if (ticketForm.description) description += `\n补充说明：${ticketForm.description}`

    const res = await createTicket({
      type: ticketForm.type,
      title: ticketForm.title,
      description: description
    })

    const ticketNo = res.data?.ticket_no || '未知'
    ticketDialogVisible.value = false

    // 在聊天记录中添加提交成功的消息
    chatStore.messages.push({
      role: 'assistant',
      content: `已提交人工请求，工单编号：${ticketNo}。你可以在"我的 - 人工请求"中查看处理进度。`,
      answer_type: 'ticket_submitted',
      source_docs: [],
      record_id: null,
      feedback: null,
      is_favorite: false,
    })
    scrollToBottom()
    ElMessage.success('工单已提交')
    chatStore.fetchConversations()
  } catch (e) {
    ElMessage.error('提交失败，请稍后重试')
  } finally {
    ticketSubmitting.value = false
  }
}

// ===== 澄清追问 =====
function needsClarification(text) {
  const hasYearLeave = text.includes('年假')
  const hasHowMany = ['几天', '多少天', '今年有几天'].some(kw => text.includes(kw))
  const hasContext = ['入职', '工龄', '工作满', '几年', '年限'].some(kw => text.includes(kw))
  return hasYearLeave && hasHowMany && !hasContext
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

// ===== 核心：发送消息 =====
async function sendMessage() {
  const q = input.value.trim()
  if (!q || loading.value) return
  input.value = ''
  chatStore.messages.push({ role: 'user', content: q })
  scrollToBottom()

  // 前端拦截：澄清追问
  if (needsClarification(q)) {
    const answer = '我需要先确认你的工龄或入职日期，才能准确计算年假天数。\n请补充以下任意一项：\n1. 入职日期\n2. 累计工作年限'
    chatStore.messages.push({
      role: 'assistant',
      content: answer,
      answer_type: 'clarification',
      source_docs: [],
      record_id: null,
      feedback: null,
      is_favorite: false,
    })
    scrollToBottom()
    // 保存到后端
    saveChatRecord({
      question: q,
      answer: answer,
      answer_type: 'clarification',
      conversation_id: chatStore.currentConversationId
    }).then(res => {
      if (res.data?.conversation_id) {
        chatStore.currentConversationId = res.data.conversation_id
      }
    }).catch(() => {})
    return
  }

  // 前端拦截：工单引导 - 直接弹出表格
  if (isTicketIntent(q)) {
    const ticketType = guessTicketType(q)
    const ticketTitle = q.replace(/^(我想|我要|我需要|我|请)/, '').trim() || '人工请求'

    // 先添加一条提示消息
    const answer = `好的，我来帮您提交"${ticketTitle}"请求，请填写以下信息：`
    chatStore.messages.push({
      role: 'assistant',
      content: answer,
      answer_type: 'ticket_form',
      source_docs: [],
      record_id: null,
      feedback: null,
      is_favorite: false,
    })
    scrollToBottom()

    // 保存到后端
    saveChatRecord({
      question: q,
      answer: answer,
      answer_type: 'ticket_form',
      conversation_id: chatStore.currentConversationId
    }).then(res => {
      if (res.data?.conversation_id) {
        chatStore.currentConversationId = res.data.conversation_id
      }
    }).catch(() => {})

    // 弹出工单表单对话框
    openTicketDialog(ticketType, ticketTitle)
    return
  }

  // 前端拦截：公告引导 - 检查权限后询问确认
  if (isNoticeIntent(q)) {
    // 检查权限：只有 HR 和管理员可以发布公告
    if (!userStore.isHR && !userStore.isAdmin) {
      const answer = '抱歉，您没有发布公告的权限。只有 HR 和管理员可以发布公告。'
      chatStore.messages.push({
        role: 'assistant',
        content: answer,
        answer_type: 'no_permission',
        source_docs: [],
        record_id: null,
        feedback: null,
        is_favorite: false,
      })
      scrollToBottom()
      // 保存到后端
      saveChatRecord({
        question: q,
        answer: answer,
        answer_type: 'no_permission',
        conversation_id: chatStore.currentConversationId
      }).then(res => {
        if (res.data?.conversation_id) {
          chatStore.currentConversationId = res.data.conversation_id
        }
      }).catch(() => {})
      return
    }

    // 如果用户直接说了具体内容（比如"通知大家明天放假"），直接弹出表单并预填
    const pureKeywords = ['发布公告', '发通知', '发布通知', '发公告', '通知公告', '通知大家', '发个公告', '发个通知', '公告', '通知']
    const isPureKeyword = pureKeywords.some(kw => q.trim() === kw || q.trim() === kw + '吧')

    if (!isPureKeyword && q.length > 6) {
      // 用户说了具体内容，直接弹出表单并预填
      let title = q.replace(/^(我想|我要|我需要|请|帮忙|帮我|发个|发一个|写个|写一个|发布公告说|发通知说|通知大家|)/, '').trim()
      if (title.length > 50) title = ''
      noticeForm.title = title
      noticeForm.content = q.includes('：') || q.includes(':') ? q.split(/[:：]/).slice(1).join(':').trim() : ''

      const answer = '好的，我来帮您发布公告，请确认或补充以下信息：'
      chatStore.messages.push({
        role: 'assistant',
        content: answer,
        answer_type: 'notice_form',
        source_docs: [],
        record_id: null,
        feedback: null,
        is_favorite: false,
      })
      scrollToBottom()
      // 保存到后端
      saveChatRecord({
        question: q,
        answer: answer,
        answer_type: 'notice_form',
        conversation_id: chatStore.currentConversationId
      }).then(res => {
        if (res.data?.conversation_id) {
          chatStore.currentConversationId = res.data.conversation_id
        }
      }).catch(() => {})
      openNoticeDialog()
      return
    }

    // 否则询问用户确认
    const answer = '您想要发布公告吗？\n\n请回复"确认"继续，或者直接告诉我公告内容，例如："通知大家明天放假一天"'
    chatStore.messages.push({
      role: 'assistant',
      content: answer,
      answer_type: 'notice_confirm',
      source_docs: [],
      record_id: null,
      feedback: null,
      is_favorite: false,
    })
    scrollToBottom()
    // 保存到后端
    saveChatRecord({
      question: q,
      answer: answer,
      answer_type: 'notice_confirm',
      conversation_id: chatStore.currentConversationId
    }).then(res => {
      if (res.data?.conversation_id) {
        chatStore.currentConversationId = res.data.conversation_id
      }
    }).catch(() => {})
    return
  }

  // 前端拦截：检查是否是公告确认操作
  const lastMsg = chatStore.messages[chatStore.messages.length - 2]
  if (lastMsg?.answer_type === 'notice_confirm') {
    // 确认词列表
    const confirmWords = ['确认', '确定', '是', '好的', '可以', '对', '嗯', '行', '好', '发吧', '发布吧', 'ok', 'OK', 'yes']
    const isConfirm = confirmWords.some(w => q.trim().toLowerCase() === w.toLowerCase())

    if (isConfirm) {
      // 用户确认后，弹出公告表单
      const answer = '好的，请填写公告信息：'
      chatStore.messages.push({
        role: 'assistant',
        content: answer,
        answer_type: 'notice_form',
        source_docs: [],
        record_id: null,
        feedback: null,
        is_favorite: false,
      })
      scrollToBottom()
      // 保存到后端
      saveChatRecord({
        question: q,
        answer: answer,
        answer_type: 'notice_form',
        conversation_id: chatStore.currentConversationId
      }).then(res => {
        if (res.data?.conversation_id) {
          chatStore.currentConversationId = res.data.conversation_id
        }
      }).catch(() => {})
      openNoticeDialog()
      return
    }

    // 用户没有确认，而是直接说了公告内容
    if (q.length > 4) {
      let title = q.replace(/^(我想|我要|我需要|请|帮忙|帮我|发个|发一个|写个|写一个|)/, '').trim()
      if (title.length > 50) title = ''
      noticeForm.title = title
      noticeForm.content = ''

      const answer = '好的，我来帮您发布公告，请确认或补充以下信息：'
      chatStore.messages.push({
        role: 'assistant',
        content: answer,
        answer_type: 'notice_form',
        source_docs: [],
        record_id: null,
        feedback: null,
        is_favorite: false,
      })
      scrollToBottom()
      // 保存到后端
      saveChatRecord({
        question: q,
        answer: answer,
        answer_type: 'notice_form',
        conversation_id: chatStore.currentConversationId
      }).then(res => {
        if (res.data?.conversation_id) {
          chatStore.currentConversationId = res.data.conversation_id
        }
      }).catch(() => {})
      openNoticeDialog()
      return
    }
  }

  // 正常调用后端
  loading.value = true
  try {
    const res = await sendChat({ question: q, conversation_id: chatStore.currentConversationId })
    const data = res.data
    chatStore.messages.push({
      role: 'assistant',
      content: data.answer,
      answer_type: data.answer_type,
      source_docs: data.source_docs || [],
      record_id: data.record_id,
      feedback: null,
      is_favorite: false,
    })
    // 更新URL
    const convId = data.conversation_id
    if (convId && route.params.conversationId !== convId) {
      const draftNotes = localStorage.getItem(notesKey(null)) || ''
      if (draftNotes && !localStorage.getItem(notesKey(convId))) {
        localStorage.setItem(notesKey(convId), draftNotes)
        localStorage.removeItem(notesKey(null))
      }
      chatStore.currentConversationId = convId
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
</style>
