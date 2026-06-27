import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import ProductCompare from '../views/ProductCompare.vue'
import ReportView from '../views/ReportView.vue'
import FeedbackView from '../views/FeedbackView.vue'
import CategoryManage from '../views/CategoryManage.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/compare',
    name: 'ProductCompare',
    component: ProductCompare
  },
  {
    path: '/reports',
    name: 'ReportView',
    component: ReportView
  },
  {
    path: '/feedback',
    name: 'FeedbackView',
    component: FeedbackView
  },
  {
    path: '/categories',
    name: 'CategoryManage',
    component: CategoryManage
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router