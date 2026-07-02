import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('../components/Layout.vue'),
    redirect: '/chat',
    meta: { requiresAuth: true },
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('../views/Dashboard.vue'), meta: { title: '首页' } },
      { path: 'chat', name: 'Chat', component: () => import('../views/Chat.vue'), meta: { title: '智能问答' } },
      { path: 'chat/:conversationId', name: 'ChatConversation', component: () => import('../views/Chat.vue'), meta: { title: '智能问答' } },
      { path: 'search', name: 'Search', component: () => import('../views/Search.vue'), meta: { title: '关键词搜索' } },
      { path: 'documents', name: 'Documents', component: () => import('../views/Documents.vue'), meta: { title: '制度文档', roles: ['hr', 'admin'] } },
      { path: 'faqs', name: 'FAQs', component: () => import('../views/FAQs.vue'), meta: { title: '标准答案库' } },
      { path: 'rules', name: 'Rules', component: () => import('../views/Rules.vue'), meta: { title: '规则问答', roles: ['hr'] } },
      { path: 'history', name: 'ChatHistory', component: () => import('../views/ChatHistory.vue'), meta: { title: '问答历史' } },
      { path: 'feedback', name: 'Feedback', component: () => import('../views/Feedback.vue'), meta: { title: '反馈纠错' } },
      { path: 'comments', name: 'Comments', component: () => import('../views/Comments.vue'), meta: { title: '评论讨论' } },
      { path: 'notices', name: 'Notices', component: () => import('../views/Notices.vue'), meta: { title: '通知公告' } },
      { path: 'tickets', name: 'Tickets', component: () => import('../views/Tickets.vue'), meta: { title: '工单系统' } },
      { path: 'onboarding', name: 'Onboarding', component: () => import('../views/Onboarding.vue'), meta: { title: '入职引导' } },
      { path: 'reminders', name: 'Reminders', component: () => import('../views/Reminders.vue'), meta: { title: '到期提醒' } },
      { path: 'statistics', name: 'Statistics', component: () => import('../views/Statistics.vue'), meta: { title: '数据统计', roles: ['hr'] } },
      { path: 'gaps', name: 'Gaps', component: () => import('../views/Gaps.vue'), meta: { title: '知识缺口', roles: ['hr'] } },
      { path: 'roi', name: 'ROI', component: () => import('../views/ROI.vue'), meta: { title: 'ROI分析', roles: ['hr'] } },
      { path: 'user-management', name: 'UserManagement', component: () => import('../views/UserManagement.vue'), meta: { title: '用户管理', roles: ['admin'] } },
      { path: 'department-management', name: 'DepartmentManagement', component: () => import('../views/DepartmentManagement.vue'), meta: { title: '部门管理', roles: ['admin'] } },
      { path: 'profile', name: 'Profile', component: () => import('../views/Profile.vue'), meta: { title: '个人信息' } },
      { path: 'my', name: 'MyPage', component: () => import('../views/MyPage.vue'), meta: { title: '我的' } }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// admin 只能访问的页面白名单
const adminAllowed = ['/documents', '/user-management', '/department-management', '/profile']

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth !== false && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    next(user.role === 'admin' ? '/user-management' : '/chat')
  } else {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    // admin 角色：只允许白名单页面
    if (user.role === 'admin' && !adminAllowed.includes(to.path)) {
      next('/user-management')
    } else if (to.meta.roles) {
      if (to.meta.roles.includes(user.role)) {
        next()
      } else {
        next(user.role === 'admin' ? '/user-management' : '/chat')
      }
    } else {
      next()
    }
  }
})

export default router