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

    <!-- 右侧聊天区域 -->
    <div class="chat-main">
      <div class="chat-messages" ref="messagesRef">
        <div class="welcome" v-if="chatStore.messages.length === 0">
          <el-icon :size="60" color="#D97706"><ChatDotRound /></el-icon>
          <h2>HR 智能助手</h2>
          <p>您好！我是公司HR制度智能问答助手，可以回答关于公司制度、考勤、休假、薪酬等问题。</p>
          <div class="quick-questions">
            <el-tag v-for="q in quickQuestions" :key="q" effect="plain" style="cursor: pointer; margin: 4px" @click="sendQuick(q)">{{ q }}</el-tag>
          </div>
        </div>
        <div v-for="(msg, idx) in chatStore.messages" :key="idx" :class="['message', msg.role]">
          <el-avatar v-if="msg.role === 'user'" :size="36" style="background: #D97706; color: #fff">{{ userStore.userInfo.real_name?.[0] || 'U' }}</el-avatar>
          <el-avatar v-else :size="36" style="background: #D97706; color: #fff"><ChatDotRound /></el-avatar>
          <div class="message-content">
            <div class="message-bubble" :class="msg.role">
              <div v-html="formatMessage(msg.content)"></div>
            </div>
            <div v-if="msg.role === 'assistant' && msg.answer_type" class="answer-type-tag">
              <el-tag v-if="msg.answer_type === 'faq'" type="success" size="small" effect="plain">FAQ 回答</el-tag>
              <el-tag v-else-if="msg.answer_type === 'rule'" type="warning" size="small" effect="plain">规则回答</el-tag>
              <el-tag v-else-if="msg.answer_type === 'rag'" type="primary" size="small" effect="plain">RAG 回答</el-tag>
              <el-tag v-else-if="msg.answer_type === 'miss'" type="info" size="small" effect="plain">未命中</el-tag>
              <el-tag v-else size="small" effect="plain">{{ msg.answer_type }}</el-tag>
            </div>
            <div v-if="msg.role === 'assistant' && msg.source_docs?.length" class="source-docs">
              <el-divider content-position="left"><span style="font-size: 12px; color: #9CA3AF">引用来源</span></el-divider>
              <el-tag v-for="(doc, i) in msg.source_docs" :key="i" size="small" type="info" style="margin: 2px">{{ doc.title || doc.question || doc.name || '来源' + (i+1) }}</el-tag>
            </div>
            <div v-if="msg.role === 'assistant' && msg.record_id" class="message-actions">
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
        <div class="input-toolbar">
          <el-tooltip content="语音问答 (Mock)" placement="top">
            <el-button :icon="Microphone" circle size="small" @click="handleVoice" />
          </el-tooltip>
          <el-tooltip content="图片问答 (Mock)" placement="top">
            <el-upload :show-file-list="false" :before-upload="handleImage" accept="image/*">
              <el-button :icon="Picture" circle size="small" />
            </el-upload>
          </el-tooltip>
          <el-tooltip content="新建对话" placement="top">
            <el-button :icon="RefreshRight" circle size="small" @click="startNewChat" />
          </el-tooltip>
          <el-tooltip content="查看历史" placement="top">
            <el-button :icon="Clock" circle size="small" @click="$router.push('/history')" />
          </el-tooltip>
        </div>
        <el-input v-model="input" placeholder="请输入您的问题... (Shift+Enter换行，Enter发送)" size="large" type="textarea" :autosize="{ minRows: 1, maxRows: 4 }" @keydown="handleKeydown" :disabled="loading" />
        <div style="display: flex; justify-content: flex-end; margin-top: 8px">
          <el-button type="primary" :icon="Promotion" @click="sendMessage" :loading="loading">发送</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Promotion, ChatDotRound, Star, Select, CloseBold, Microphone, Picture, RefreshRight, Clock, Plus, Delete } from '@element-plus/icons-vue'
import { sendChat, voiceChat, imageChat } from '../api/chat'
import { getRecommendations } from '../api/recommendations'
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
const quickQuestions = ref(['年假怎么计算？', '请假需要提前多久？', '报销流程是什么？', '绩效申诉怎么提交？'])

const dateGroupLabels = {
  today: '今天',
  yesterday: '昨天',
  last_7_days: '近7天',
  last_30_days: '近30天',
  earlier: '更早',
}

function dateGroupLabel(label) {
  return dateGroupLabels[label] || label
}

function formatMessage(text) {
  if (!text) return ''
  return text.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
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
    if (route.params.conversationId === convId) {
      router.push('/chat')
    }
    ElMessage.success('已删除')
  } catch {}
}

async function sendMessage() {
  const q = input.value.trim()
  if (!q || loading.value) return
  input.value = ''
  chatStore.messages.push({ role: 'user', content: q })
  scrollToBottom()
  loading.value = true
  try {
    const res = await sendChat({ question: q, conversation_id: chatStore.currentConversationId })
    const convId = res.data.conversation_id
    chatStore.currentConversationId = convId
    chatStore.messages.push({
      role: 'assistant',
      content: res.data.answer,
      answer_type: res.data.answer_type,
      source_docs: res.data.source_docs,
      record_id: res.data.record_id,
      feedback: null,
      is_favorite: false,
    })
    // 更新URL（不触发路由跳转）
    if (route.params.conversationId !== convId) {
      router.replace('/chat/' + convId)
    }
    // 刷新侧边栏
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

async function handleVoice() {
  loading.value = true
  try {
    const res = await voiceChat()
    chatStore.messages.push({ role: 'user', content: `[语音输入] ${res.data.recognized_text}` })
    chatStore.messages.push({
      role: 'assistant', content: res.data.answer, answer_type: 'mock',
      source_docs: [], record_id: null, feedback: null, is_favorite: false,
    })
    scrollToBottom()
  } catch (e) {
    ElMessage.error('语音识别失败')
  } finally {
    loading.value = false
  }
}

async function handleImage(file) {
  loading.value = true
  try {
    const res = await imageChat()
    chatStore.messages.push({ role: 'user', content: `[图片上传] ${res.data.ocr_text}` })
    chatStore.messages.push({
      role: 'assistant', content: res.data.answer, answer_type: 'mock',
      source_docs: [], record_id: null, feedback: null, is_favorite: false,
    })
    scrollToBottom()
  } catch (e) {
    ElMessage.error('图片识别失败')
  } finally {
    loading.value = false
  }
  return false
}

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

// 路由参数变化时加载对应对话
watch(() => route.params.conversationId, (newId) => {
  if (newId) {
    chatStore.loadConversation(newId)
  } else {
    chatStore.clearCurrentConversation()
  }
})

onMounted(async () => {
  // 加载对话列表
  chatStore.fetchConversations()
  // 加载推荐问题
  try {
    const res = await getRecommendations()
    if (res.data?.length) quickQuestions.value = res.data.map(r => r.question)
  } catch (e) {}
  // 如果URL带conversationId，加载该对话
  if (route.params.conversationId) {
    chatStore.loadConversation(route.params.conversationId)
  }
  // 如果URL带q参数，直接发送
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
.welcome { text-align: center; padding: 80px 20px; }
.welcome h2 { margin: 16px 0 8px; color: #111827; font-weight: 700; letter-spacing: -0.3px; }
.welcome p { color: #9CA3AF; margin-bottom: 24px; font-size: 15px; }
.quick-questions { display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; }
.message { display: flex; gap: 12px; margin-bottom: 24px; }
.message.user { flex-direction: row-reverse; }
.message-content { max-width: 70%; }
.message-bubble { padding: 14px 18px; border-radius: 16px; line-height: 1.7; font-size: 14px; }
.message-bubble.user { background: #D97706; color: #fff; border-top-right-radius: 4px; }
.message-bubble.assistant { background: #f9fafb; color: #111827; border-top-left-radius: 4px; border: 1px solid #f3f4f6; }
.message-actions { margin-top: 8px; display: flex; gap: 8px; }
.answer-type-tag { margin-top: 6px; }
.source-docs { margin-top: 8px; }
.loading-bubble { display: flex; gap: 6px; align-items: center; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: #D97706; opacity: 0.4; animation: bounce 1.4s infinite ease-in-out both; }
.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }
@keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
.chat-input { padding: 16px 20px; border-top: 1px solid #f3f4f6; }
.input-toolbar { display: flex; gap: 8px; margin-bottom: 8px; }
</style>
