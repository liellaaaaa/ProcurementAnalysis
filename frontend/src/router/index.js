import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue')
  },
  {
    path: '/compare',
    name: 'ProductCompare',
    component: () => import('../views/ProductCompare.vue')
  },
  {
    path: '/reports',
    name: 'ReportView',
    component: () => import('../views/ReportView.vue')
  },
  {
    path: '/feedback',
    name: 'FeedbackView',
    component: () => import('../views/FeedbackView.vue')
  },
  {
    path: '/categories',
    name: 'CategoryManage',
    component: () => import('../views/CategoryManage.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router