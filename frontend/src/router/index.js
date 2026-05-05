import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import ProductCompare from '../views/ProductCompare.vue'
import ProductManage from '../views/ProductManage.vue'
import ReportView from '../views/ReportView.vue'
import AlertView from '../views/AlertView.vue'

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
    path: '/manage',
    name: 'ProductManage',
    component: ProductManage
  },
  {
    path: '/reports',
    name: 'ReportView',
    component: ReportView
  },
  {
    path: '/alerts',
    name: 'AlertView',
    component: AlertView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router