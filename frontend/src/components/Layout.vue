<template>
  <el-container style="height: 100vh">
    <el-aside :width="isCollapse ? '64px' : '220px'" class="sidebar">
      <div class="logo" :style="{ padding: isCollapse ? '20px 8px' : '20px 20px' }">
        <el-icon :size="22" color="#D97706"><ChatDotRound /></el-icon>
        <span v-if="!isCollapse" class="logo-text">HR Copilot</span>
      </div>
      <el-menu
        :default-active="$route.path"
        :collapse="isCollapse"
        background-color="transparent"
        text-color="#6B7280"
        active-text-color="#D97706"
        router
        :collapse-transition="false"
        class="sidebar-menu"
      >
        <el-menu-item index="/dashboard">
          <el-icon><HomeFilled /></el-icon>
          <template #title>首页</template>
        </el-menu-item>
        <el-menu-item index="/chat">
          <el-icon><ChatDotRound /></el-icon>
          <template #title>智能问答</template>
        </el-menu-item>
        <el-menu-item index="/search">
          <el-icon><Search /></el-icon>
          <template #title>关键词搜索</template>
        </el-menu-item>
        <el-menu-item index="/faqs">
          <el-icon><QuestionFilled /></el-icon>
          <template #title>FAQ</template>
        </el-menu-item>
        <el-menu-item index="/notices">
          <el-icon><Bell /></el-icon>
          <template #title>通知公告</template>
          <el-badge v-if="unreadCount > 0" :value="unreadCount" :max="99" class="notice-badge" />
        </el-menu-item>
        <el-menu-item index="/tickets">
          <el-icon><Tickets /></el-icon>
          <template #title>工单系统</template>
        </el-menu-item>
        <el-menu-item index="/history">
          <el-icon><Clock /></el-icon>
          <template #title>问答历史</template>
        </el-menu-item>
        <el-menu-item index="/feedback">
          <el-icon><Comment /></el-icon>
          <template #title>反馈纠错</template>
        </el-menu-item>
        <el-menu-item index="/comments">
          <el-icon><ChatLineSquare /></el-icon>
          <template #title>评论讨论</template>
        </el-menu-item>
        <el-menu-item index="/onboarding">
          <el-icon><Reading /></el-icon>
          <template #title>入职引导</template>
        </el-menu-item>
        <el-menu-item index="/reminders">
          <el-icon><AlarmClock /></el-icon>
          <template #title>到期提醒</template>
        </el-menu-item>
        <template v-if="userStore.isHR">
          <el-sub-menu index="hr-menu">
            <template #title>
              <el-icon><Setting /></el-icon>
              <span>HR管理</span>
            </template>
            <el-menu-item index="/documents">制度文档</el-menu-item>
            <el-menu-item index="/rules">规则问答</el-menu-item>
            <el-menu-item index="/statistics">数据统计</el-menu-item>
            <el-menu-item index="/gaps">知识缺口</el-menu-item>
            <el-menu-item index="/roi">ROI分析</el-menu-item>
          </el-sub-menu>
        </template>
        <template v-if="userStore.isAdmin">
          <el-sub-menu index="admin-menu">
            <template #title>
              <el-icon><UserFilled /></el-icon>
              <span>系统管理</span>
            </template>
            <el-menu-item index="/user-management">用户管理</el-menu-item>
            <el-menu-item index="/department-management">部门管理</el-menu-item>
          </el-sub-menu>
        </template>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="top-header">
        <div style="display: flex; align-items: center">
          <el-icon :size="20" style="cursor: pointer; color: #6B7280" @click="isCollapse = !isCollapse"><Fold v-if="!isCollapse" /><Expand v-else /></el-icon>
          <el-breadcrumb separator="/" style="margin-left: 16px">
            <el-breadcrumb-item>{{ $route.meta.title || '首页' }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <el-dropdown trigger="click">
          <span style="cursor: pointer; display: flex; align-items: center">
            <el-avatar :size="32" style="background: #D97706; color: #fff">{{ userStore.userInfo.real_name?.[0] || 'U' }}</el-avatar>
            <span style="margin-left: 8px; color: #374151">{{ userStore.userInfo.real_name || '用户' }}</span>
            <el-icon style="margin-left: 4px; color: #9CA3AF"><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="$router.push('/profile')">个人信息</el-dropdown-item>
              <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { getUnreadCount } from '../api/notices'

const router = useRouter()
const userStore = useUserStore()
const isCollapse = ref(true)
const unreadCount = ref(0)

async function fetchUnread() {
  try {
    const res = await getUnreadCount()
    unreadCount.value = res.data?.unread || 0
  } catch (e) {}
}

function handleLogout() {
  userStore.logout()
  router.push('/login')
}

onMounted(() => {
  fetchUnread()
})
</script>

<style scoped>
.sidebar {
  background: #ffffff;
  border-right: 1px solid #f3f4f6;
  transition: width 0.3s;
}
.logo {
  display: flex;
  align-items: center;
  height: 56px;
  gap: 10px;
  border-bottom: 1px solid #f3f4f6;
}
.logo-text {
  color: #111827;
  font-size: 17px;
  font-weight: 700;
  white-space: nowrap;
  letter-spacing: -0.3px;
}
.sidebar-menu {
  padding: 8px;
}
.sidebar-menu .el-menu-item,
.sidebar-menu :deep(.el-sub-menu__title) {
  border-radius: 8px;
  margin-bottom: 2px;
  height: 40px;
  line-height: 40px;
}
.sidebar-menu .el-menu-item:hover,
.sidebar-menu :deep(.el-sub-menu__title:hover) {
  background-color: #f9fafb;
}
.sidebar-menu .el-menu-item.is-active {
  background-color: #FFF7ED;
  color: #D97706;
  font-weight: 500;
}
.notice-badge {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
}
.top-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #f3f4f6;
  background: #ffffff;
  padding: 0 24px;
  height: 56px;
}
.main-content {
  background: #fafafa;
  padding: 24px;
}
@media (max-width: 768px) {
  .logo-text { display: none; }
}
</style>