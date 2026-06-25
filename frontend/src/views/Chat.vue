<template>
  <div class="chat-container">
    <div class="chat-messages" ref="messagesRef">
      <div class="welcome" v-if="messages.length === 0">
        <el-icon :size="60" color="#1890ff"><ChatDotRound /></el-icon>
        <h2>HR 智能助手</h2>
        <p>您好！我是公司HR制度智能问答助手，可以回答关于公司制度、考勤、休假、薪酬等问题。</p>
        <div class="quick-questions">
          <el-tag v-for="q in quickQuestions" :key="q" effect="plain" style="cursor: pointer; margin: 4px" @click="sendQuick(q)">{{ q }}</el-tag>
        </div>
      </div>
      <div v-for="(msg, idx) in messages" :key="idx" :class="['message', msg.role]">
        <el-avatar v-if="msg.role === 'user'" :size="36" style="background: #1890ff">{{ userStore.userInfo.real_name?.[0] || 'U' }}</el-avatar>
        <el-avatar v-else :size="36" style="background: #52c41a"><ChatDotRound /></el-avatar>
        <div class="message-content">
          <div class="message-bubble" :class="msg.role">
            <div v-html="formatMessage(msg.content)"></div>
          </div>
          <div v-if="msg.role === 'assistant' && msg.source_docs?.length" class="source-docs">
            <el-divider content-position="left"><span style="font-size: 12px; color: #999">引用来源</span></el-divider>
            <el-tag v-for="(doc, i) in msg.source_docs" :key="i" size="small" type="info" style="margin: 2px">{{ doc.title || doc.question || '来源' + (i+1) }}</el-tag>
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
        <el-avatar :size="36" style="background: #52c41a"><ChatDotRound /></el-avatar>
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
          <el-button :icon="RefreshRight" circle size="small" @click="newConversation" />
        </el-tooltip>
      </div>
      <el-input v-model="input" placeholder="请输入您的问题... (Shift+Enter换行，Enter发送)" size="large" type="textarea" :autosize="{ minRows: 1, maxRows: 4 }" @keydown="handleKeydown" :disabled="loading" />
      <div style="display: flex; justify-content: flex-end; margin-top: 8px">
        <el-button type="primary" :icon="Promotion" @click="sendMessage" :loading="loading">发送</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Promotion, ChatDotRound, Star, Select, CloseBold, Microphone, Picture, RefreshRight } from '@element-plus/icons-vue'
import { sendChat, voiceChat, imageChat } from '../api/chat'
import { getRecommendations } from '../api/recommendations'
import { createFeedback } from '../api/feedback'
import { toggleFavorite } from '../api/chatHistory'
import { useUserStore } from '../stores/user'

const route = useRoute()
const userStore = useUserStore()
const messagesRef = ref()
const input = ref('')
const loading = ref(false)
const messages = ref([])
const conversationId = ref(null)
const quickQuestions = ref(['年假怎么计算？', '请假需要提前多久？', '报销流程是什么？', '绩效申诉怎么提交？'])

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

function newConversation() {
  messages.value = []
  conversationId.value = null
  input.value = ''
}

async function sendMessage() {
  const q = input.value.trim()
  if (!q || loading.value) return
  input.value = ''
  messages.value.push({ role: 'user', content: q })
  scrollToBottom()
  loading.value = true
  try {
    const res = await sendChat({ question: q, conversation_id: conversationId.value })
    conversationId.value = res.data.conversation_id || conversationId.value
    messages.value.push({
      role: 'assistant',
      content: res.data.answer,
      answer_type: res.data.answer_type,
      source_docs: res.data.source_docs,
      record_id: res.data.record_id,
      feedback: null,
      is_favorite: false
    })
  } catch (e) {
    messages.value.push({ role: 'assistant', content: '抱歉，发生了错误，请稍后重试。' })
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
    messages.value.push({ role: 'user', content: `[语音输入] ${res.data.recognized_text}` })
    messages.value.push({
      role: 'assistant',
      content: res.data.answer,
      answer_type: 'mock',
      source_docs: [],
      record_id: null,
      feedback: null,
      is_favorite: false
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
    messages.value.push({ role: 'user', content: `[图片上传] ${res.data.ocr_text}` })
    messages.value.push({
      role: 'assistant',
      content: res.data.answer,
      answer_type: 'mock',
      source_docs: [],
      record_id: null,
      feedback: null,
      is_favorite: false
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

onMounted(async () => {
  try {
    const res = await getRecommendations()
    if (res.data?.length) quickQuestions.value = res.data.map(r => r.question)
  } catch (e) {}
  if (route.query.q) {
    input.value = route.query.q
    sendMessage()
  }
})
</script>

<style scoped>
.chat-container { display: flex; flex-direction: column; height: calc(100vh - 120px); background: #fff; border-radius: 8px; overflow: hidden; }
.chat-messages { flex: 1; overflow-y: auto; padding: 20px; }
.welcome { text-align: center; padding: 60px 20px; }
.welcome h2 { margin: 16px 0 8px; color: #333; }
.welcome p { color: #999; margin-bottom: 20px; }
.quick-questions { display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; }
.message { display: flex; gap: 12px; margin-bottom: 20px; }
.message.user { flex-direction: row-reverse; }
.message-content { max-width: 70%; }
.message-bubble { padding: 12px 16px; border-radius: 12px; line-height: 1.6; font-size: 14px; }
.message-bubble.user { background: #1890ff; color: #fff; border-top-right-radius: 4px; }
.message-bubble.assistant { background: #f5f5f5; color: #333; border-top-left-radius: 4px; }
.message-actions { margin-top: 8px; display: flex; gap: 8px; }
.source-docs { margin-top: 8px; }
.loading-bubble { display: flex; gap: 6px; align-items: center; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: #999; animation: bounce 1.4s infinite ease-in-out both; }
.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }
@keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
.chat-input { padding: 16px; border-top: 1px solid #e8e8e8; }
.input-toolbar { display: flex; gap: 8px; margin-bottom: 8px; }
</style>
