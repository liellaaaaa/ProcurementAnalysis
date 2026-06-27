import axios from 'axios'

const API_BASE = '/api/v1'

// 获取 token
export function getToken() {
  return localStorage.getItem('token')
}

// 设置 token
export function setToken(token) {
  localStorage.setItem('token', token)
}

// 删除 token
export function removeToken() {
  localStorage.removeItem('token')
}

// axios 实例（带 token 自动注入）
const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
})

// 请求拦截器：自动带上 token
api.interceptors.request.use(config => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：token 过期则跳转登录
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      removeToken()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api

// 登录
export const authApi = {
  login: (username, password) =>
    api.post('/auth/login', { username, password }),
  logout: () =>
    api.post('/auth/logout'),
  me: () =>
    api.get('/auth/me'),
}

// 更新日志
export const updateLogApi = {
  getLogs: () =>
    api.get('/update-logs'),
}
