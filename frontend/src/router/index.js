import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '../api/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/compare',
    name: 'ProductCompare',
    component: () => import('../views/ProductCompare.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/reports',
    name: 'ReportView',
    component: () => import('../views/ReportView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/feedback',
    name: 'FeedbackView',
    component: () => import('../views/FeedbackView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/categories',
    name: 'CategoryManage',
    component: () => import('../views/CategoryManage.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = getToken()
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/')
  } else {
    next()
  }
})

export default router
