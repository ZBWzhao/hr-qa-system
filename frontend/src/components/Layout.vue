<template>
  <el-container style="height: 100vh">
    <el-aside width="220px" class="sidebar">
      <div class="logo" style="padding: 20px 20px">
        <el-icon :size="22" color="#D97706"><ChatDotRound /></el-icon>
        <span class="logo-text">HR Copilot</span>
      </div>
      <el-menu
        :default-active="$route.path"
        :collapse="false"
        background-color="transparent"
        text-color="#6B7280"
        active-text-color="#D97706"
        router
        :collapse-transition="false"
        class="sidebar-menu"
      >
        <!-- 员工端：精简为3个入口 -->
        <template v-if="!userStore.isHR && !userStore.isAdmin">
          <el-menu-item index="/chat">
            <el-icon><ChatDotRound /></el-icon>
            <template #title>智能问答</template>
          </el-menu-item>
          <el-menu-item index="/notices">
            <el-icon><Bell /></el-icon>
            <template #title>
              <div style="display: flex; align-items: center; width: 100%">
                <span>通知公告</span>
                <el-badge v-if="unreadCount > 0" :value="unreadCount" :max="99" style="margin-left: auto; margin-top: -6px" />
              </div>
            </template>
          </el-menu-item>
          <el-menu-item index="/my">
            <el-icon><User /></el-icon>
            <template #title>我的</template>
          </el-menu-item>
        </template>

        <!-- HR端：知识库运营 -->
        <template v-if="userStore.isHR">
          <el-menu-item index="/chat">
            <el-icon><ChatDotRound /></el-icon>
            <template #title>智能问答</template>
          </el-menu-item>
          <el-menu-item index="/todo">
            <el-icon><Tickets /></el-icon>
            <template #title>
              <div style="display: flex; align-items: center; width: 100%">
                <span>待办中心</span>
                <el-badge v-if="pendingTickets > 0" :value="pendingTickets" :max="99" style="margin-left: auto; margin-top: -6px" />
              </div>
            </template>
          </el-menu-item>
          <el-menu-item index="/knowledge">
            <el-icon><Folder /></el-icon>
            <template #title>知识管理</template>
          </el-menu-item>
          <el-menu-item index="/notices">
            <el-icon><Bell /></el-icon>
            <template #title>
              <div style="display: flex; align-items: center; width: 100%">
                <span>通知发布</span>
                <el-badge v-if="unreadCount > 0" :value="unreadCount" :max="99" style="margin-left: auto; margin-top: -6px" />
              </div>
            </template>
          </el-menu-item>
          <el-menu-item index="/statistics">
            <el-icon><DataAnalysis /></el-icon>
            <template #title>数据看板</template>
          </el-menu-item>
        </template>

        <!-- 管理员端：运维管理 -->
        <template v-if="userStore.isAdmin">
          <el-menu-item index="/user-management">
            <el-icon><UserFilled /></el-icon>
            <template #title>用户与角色</template>
          </el-menu-item>
          <el-menu-item index="/department-management">
            <el-icon><OfficeBuilding /></el-icon>
            <template #title>系统配置</template>
          </el-menu-item>
          <el-menu-item index="/documents">
            <el-icon><Folder /></el-icon>
            <template #title>数据维护</template>
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="top-header">
        <div style="display: flex; align-items: center">
          <el-breadcrumb separator="/">
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
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { getUnreadCount } from '../api/notices'
import { getTicketStats } from '../api/tickets'

const router = useRouter()
const userStore = useUserStore()
const unreadCount = ref(0)
const pendingTickets = ref(0)

async function fetchUnread() {
  try {
    const res = await getUnreadCount()
    unreadCount.value = res.data?.unread || 0
  } catch (e) {}
}

async function fetchTicketStats() {
  if (!userStore.isHR) return
  try {
    const res = await getTicketStats()
    pendingTickets.value = res.data?.pending || 0
  } catch (e) {}
}

async function handleLogout() {
  // 先清除数据
  userStore.logout()
  // 等待下一个 tick 确保数据清除完成
  await nextTick()
  // 然后跳转
  router.push('/login')
}

onMounted(() => {
  fetchUnread()
  fetchTicketStats()
})
</script>

<style scoped>
.sidebar {
  background: #ffffff;
  border-right: 1px solid #f3f4f6;
  transition: width 0.15s ease;
  overflow: hidden;
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
  transition: background-color 0.2s ease, color 0.2s ease;
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
/* 侧边栏折叠时tooltip无延迟消失 */
:global(.el-popper.el-menu__tooltip.is-dark) {
  --el-popper-hide-after: 0;
}
:global(.el-popper.el-menu__tooltip) {
  transition: opacity 0.08s ease-out !important;
}
/* 防止菜单项hover时的闪烁 */
.sidebar-menu .el-menu-item,
.sidebar-menu :deep(.el-sub-menu) {
  will-change: background-color;
  transform: translateZ(0);
}

@media (max-width: 768px) {
  .logo-text { display: none; }
}
</style>