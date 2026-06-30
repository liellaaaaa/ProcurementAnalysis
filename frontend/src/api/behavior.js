/**
 * 行为日志分析 API 客户端
 */
import axios from 'axios'

const API_BASE = '/api/v1'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000
})

// 请求拦截器：带上 token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  const sid = sessionStorage.getItem('bt_sid')
  if (sid) {
    config.headers['X-Session-ID'] = sid
  }
  return config
})

// 行为分析 API
export const behaviorApi = {
  // 漏斗分析
  getFunnel(params) {
    return api.get('/operation-logs/funnel', { params })
  },

  // 热力图数据
  getHeatmap(params) {
    return api.get('/operation-logs/heatmap', { params })
  },

  // 留存统计
  getRetention(params) {
    return api.get('/operation-logs/retention', { params })
  },

  // 日志列表（带行为日志筛选）
  getLogs(params) {
    return api.get('/operation-logs', { params })
  },

  // 统计摘要
  getSummary(params) {
    return api.get('/operation-logs/summary', { params })
  }
}

export default api
