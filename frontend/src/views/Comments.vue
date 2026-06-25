<template>
  <el-card>
    <template #header><span style="font-weight: 700">评论讨论</span></template>

    <div style="display: flex; gap: 12px; margin-bottom: 20px">
      <el-select v-model="targetType" placeholder="选择类型" style="width: 120px" @change="fetchComments">
        <el-option label="FAQ" value="faq" />
        <el-option label="文档" value="document" />
      </el-select>
      <el-select v-model="targetId" :placeholder="targetType === 'faq' ? '选择FAQ' : '选择文档'" style="width: 300px" @change="fetchComments" filterable>
        <el-option v-for="item in targetOptions" :key="item.id" :label="item.title || item.question" :value="item.id" />
      </el-select>
    </div>

    <div v-if="targetId" style="margin-bottom: 20px">
      <el-input v-model="newComment" type="textarea" :rows="3" placeholder="发表你的评论..." />
      <el-button type="primary" style="margin-top: 8px" @click="submitComment" :disabled="!newComment.trim()">发表评论</el-button>
    </div>

    <div v-if="!targetId" style="text-align: center; padding: 40px; color: #999">
      请选择FAQ或文档后查看评论
    </div>

    <div v-for="comment in comments" :key="comment.id" class="comment-item">
      <div style="display: flex; justify-content: space-between; align-items: center">
        <div style="display: flex; align-items: center; gap: 8px">
          <el-avatar :size="32" style="background: #1890ff">U</el-avatar>
          <span style="font-weight: 500">用户 {{ comment.user_id }}</span>
          <el-tag v-if="comment.is_adopted" type="success" size="small">已采纳</el-tag>
        </div>
        <span style="color: #999; font-size: 12px">{{ comment.created_at?.substring(0, 16) }}</span>
      </div>
      <div style="margin: 10px 0; line-height: 1.6; color: #333">{{ comment.content }}</div>
      <div style="display: flex; gap: 16px; align-items: center">
        <el-button text size="small" @click="handleLike(comment)">
          <el-icon style="margin-right: 4px"><Star /></el-icon>
          {{ comment.like_count }}
        </el-button>
        <el-button text size="small" @click="showReplyInput(comment)">回复</el-button>
        <template v-if="userStore.isHR">
          <el-button text size="small" type="success" @click="handleAdopt(comment)">采纳</el-button>
          <el-button text size="small" type="danger" @click="handleDelete(comment)">删除</el-button>
        </template>
      </div>

      <div v-if="comment.replies?.length" style="margin-left: 40px; margin-top: 12px">
        <div v-for="reply in comment.replies" :key="reply.id" class="reply-item">
          <div style="display: flex; justify-content: space-between; align-items: center">
            <div style="display: flex; align-items: center; gap: 8px">
              <el-avatar :size="24" style="background: #52c41a; font-size: 12px">R</el-avatar>
              <span style="font-size: 13px">用户 {{ reply.user_id }}</span>
            </div>
            <span style="color: #999; font-size: 12px">{{ reply.created_at?.substring(0, 16) }}</span>
          </div>
          <div style="margin: 6px 0; font-size: 13px; color: #555">{{ reply.content }}</div>
          <div style="display: flex; gap: 12px">
            <el-button text size="small" @click="handleLike(reply)">
              <el-icon style="margin-right: 2px"><Star /></el-icon> {{ reply.like_count }}
            </el-button>
            <el-button v-if="userStore.isHR" text size="small" type="danger" @click="handleDelete(reply)">删除</el-button>
          </div>
        </div>
      </div>

      <div v-if="replyTarget?.id === comment.id" style="margin-left: 40px; margin-top: 8px">
        <el-input v-model="replyContent" type="textarea" :rows="2" :placeholder="`回复用户 ${comment.user_id}...`" />
        <div style="margin-top: 6px; display: flex; gap: 8px">
          <el-button size="small" type="primary" @click="submitReply(comment)">发送</el-button>
          <el-button size="small" @click="replyTarget = null">取消</el-button>
        </div>
      </div>
    </div>

    <el-empty v-if="targetId && !comments.length" description="暂无评论，来发表第一条吧" />
  </el-card>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { Star } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getComments, createComment, likeComment, adoptComment, deleteComment } from '../api/comments'
import { getFaqs } from '../api/faqs'
import { getDocuments } from '../api/documents'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const targetType = ref('faq')
const targetId = ref(null)
const targetOptions = ref([])
const comments = ref([])
const newComment = ref('')
const replyTarget = ref(null)
const replyContent = ref('')

async function fetchOptions() {
  try {
    if (targetType.value === 'faq') {
      const res = await getFaqs({ page_size: 100 })
      targetOptions.value = res.data?.items || []
    } else {
      const res = await getDocuments({ page_size: 100 })
      targetOptions.value = res.data?.items || []
    }
  } catch (e) {
    targetOptions.value = []
  }
}

async function fetchComments() {
  if (!targetId.value) { comments.value = []; return }
  try {
    const res = await getComments({ target_type: targetType.value, target_id: targetId.value })
    comments.value = res.data || []
  } catch (e) {
    comments.value = []
  }
}

async function submitComment() {
  if (!newComment.value.trim()) return
  await createComment({ target_type: targetType.value, target_id: targetId.value, content: newComment.value })
  ElMessage.success('评论成功')
  newComment.value = ''
  fetchComments()
}

function showReplyInput(comment) {
  replyTarget.value = comment
  replyContent.value = ''
}

async function submitReply(parent) {
  if (!replyContent.value.trim()) return
  await createComment({ target_type: targetType.value, target_id: targetId.value, content: replyContent.value, parent_id: parent.id })
  ElMessage.success('回复成功')
  replyTarget.value = null
  replyContent.value = ''
  fetchComments()
}

async function handleLike(comment) {
  try {
    const res = await likeComment(comment.id)
    comment.like_count = res.data.like_count
  } catch (e) {}
}

async function handleAdopt(comment) {
  await adoptComment(comment.id)
  ElMessage.success('已采纳')
  fetchComments()
}

async function handleDelete(comment) {
  await ElMessageBox.confirm('确认删除该评论？', '提示', { type: 'warning' })
  await deleteComment(comment.id)
  ElMessage.success('已删除')
  fetchComments()
}

watch(targetType, () => {
  targetId.value = null
  comments.value = []
  fetchOptions()
})

onMounted(() => fetchOptions())
</script>

<style scoped>
.comment-item {
  padding: 16px;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  margin-bottom: 12px;
}
.reply-item {
  padding: 10px;
  border-left: 3px solid #e8e8e8;
  margin-bottom: 8px;
  background: #fafafa;
  border-radius: 4px;
}
</style>
