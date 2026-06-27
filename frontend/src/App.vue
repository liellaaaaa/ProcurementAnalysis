<template>
  <div id="app">
    <div class="bg-pattern"></div>

    <nav class="main-nav">
      <div class="nav-container">
        <div class="nav-brand">
          <div class="brand-mark">
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
              <path d="M14 2L25 8V20L14 26L3 20V8L14 2Z" stroke="currentColor" stroke-width="2" fill="none"/>
              <path d="M14 10L19 13V19L14 22L9 19V13L14 10Z" fill="currentColor"/>
            </svg>
          </div>
          <div class="brand-text">
            <span class="brand-name">Procurement</span>
            <span class="brand-tag">Analysis</span>
          </div>
        </div>

        <div class="nav-links">
          <router-link to="/" class="nav-link">
            <span class="link-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="7" height="7" rx="1"/>
                <rect x="14" y="3" width="7" height="7" rx="1"/>
                <rect x="3" y="14" width="7" height="7" rx="1"/>
                <rect x="14" y="14" width="7" height="7" rx="1"/>
              </svg>
            </span>
            <span class="link-text">数据看板</span>
          </router-link>

          <router-link to="/compare" class="nav-link">
            <span class="link-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="20" x2="18" y2="10"/>
                <line x1="12" y1="20" x2="12" y2="4"/>
                <line x1="6" y1="20" x2="6" y2="14"/>
              </svg>
            </span>
            <span class="link-text">产品对比</span>
          </router-link>

          <router-link to="/reports" class="nav-link">
            <span class="link-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
                <polyline points="10 9 9 9 8 9"/>
              </svg>
            </span>
            <span class="link-text">报表中心</span>
          </router-link>
        </div>

        <div class="nav-actions">
          <el-dropdown trigger="click" @command="handleCommand">
            <span class="nav-link user-dropdown-trigger">
              <span class="link-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
              </span>
              <span class="link-text">{{ currentUser }}</span>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="6 9 12 15 18 9"/>
              </svg>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="feedback">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 8px">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                  </svg>
                  问题与建议
                </el-dropdown-item>
                <el-dropdown-item command="updateLog">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 8px">
                    <circle cx="12" cy="12" r="10"/>
                    <polyline points="12 6 12 12 16 14"/>
                  </svg>
                  更新日志
                </el-dropdown-item>
                <el-dropdown-item divided command="logout" style="color: #e63946">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 8px">
                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                    <polyline points="16 17 21 12 16 7"/>
                    <line x1="21" y1="12" x2="9" y2="12"/>
                  </svg>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </nav>

    <!-- 问题与建议反馈弹窗 -->
    <el-dialog
      v-model="showFeedbackDialog"
      title="问题与建议"
      width="480px"
      class="feedback-dialog"
      :close-on-click-modal="false"
    >
      <div class="feedback-tip">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        为更快解决问题，问题发生时请立即反馈。
      </div>
      <el-input
        v-model="feedbackDescription"
        type="textarea"
        :rows="5"
        maxlength="500"
        placeholder="详细描述问题或建议"
        class="feedback-textarea"
      />
      <div class="feedback-char-count">{{ feedbackDescription.length }}/500</div>
      <template #footer>
        <el-button @click="showFeedbackDialog = false" class="btn-cancel">取消</el-button>
        <el-button type="primary" :loading="submittingFeedback" @click="submitFeedback" class="btn-submit-feedback">提交</el-button>
      </template>
    </el-dialog>

    <!-- 更新日志弹窗 -->
    <el-dialog
      v-model="showUpdateLogDialog"
      title="更新日志"
      width="500px"
      class="update-log-dialog"
    >
      <div v-if="loadingLogs" class="logs-loading">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>加载中...</span>
      </div>
      <div v-else-if="updateLogs.length === 0" class="logs-empty">
        暂无更新日志
      </div>
      <div v-else class="logs-list">
        <div v-for="log in updateLogs" :key="log.date" class="log-item">
          <div class="log-date">{{ log.date }}</div>
          <div class="log-content">{{ log.content }}</div>
        </div>
      </div>
    </el-dialog>

    <router-view />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElIcon } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { feedbackApi } from './api/feedback'
import { updateLogApi, getToken, removeToken } from './api/auth'

const router = useRouter()

const showFeedbackDialog = ref(false)
const feedbackDescription = ref('')
const submittingFeedback = ref(false)

const showUpdateLogDialog = ref(false)
const updateLogs = ref([])
const loadingLogs = ref(false)

const currentUser = ref('')

async function loadCurrentUser() {
  if (!getToken()) return
  try {
    const token = getToken()
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]))
        currentUser.value = payload.username || '用户'
      } catch {
        currentUser.value = '用户'
      }
    }
  } catch {
    currentUser.value = '用户'
  }
}

async function submitFeedback() {
  if (!feedbackDescription.value.trim()) {
    ElMessage.warning('请输入问题描述')
    return
  }
  submittingFeedback.value = true
  try {
    await feedbackApi.createFeedback({ description: feedbackDescription.value })
    ElMessage.success('反馈已提交，感谢您的建议')
    feedbackDescription.value = ''
    showFeedbackDialog.value = false
  } catch (e) {
    ElMessage.error('提交失败：' + (e?.response?.data?.detail || e.message || '请稍后重试'))
  } finally {
    submittingFeedback.value = false
  }
}

async function loadUpdateLogs() {
  loadingLogs.value = true
  try {
    const res = await updateLogApi.getLogs()
    updateLogs.value = res.data.logs || []
  } catch (e) {
    ElMessage.error('加载更新日志失败')
    updateLogs.value = []
  } finally {
    loadingLogs.value = false
  }
}

function handleCommand(command) {
  switch (command) {
    case 'feedback':
      showFeedbackDialog.value = true
      break
    case 'updateLog':
      loadUpdateLogs()
      showUpdateLogDialog.value = true
      break
    case 'logout':
      removeToken()
      ElMessage.success('已退出登录')
      router.push('/login')
      break
  }
}

onMounted(() => {
  loadCurrentUser()
})
</script>

<style>

:root {
  --color-primary: #0077cc;
  --color-primary-light: #00a8e8;
  --color-primary-pale: #e6f4fa;
  --color-primary-dark: #005fa3;
  --color-primary-dim: rgba(0, 119, 204, 0.1);
  --color-primary-glow: rgba(0, 119, 204, 0.15);

  --bg-primary: #f5f7fa;
  --bg-secondary: #ffffff;
  --bg-card: #ffffff;
  --bg-hover: #f0f2f5;
  --bg-elevated: #fafbfc;

  --text-primary: #1a1a2e;
  --text-secondary: #5a6178;
  --text-muted: #9ca3af;
  --el-font-size-base: 16px;

  --border-color: #e4e7ed;
  --border-light: #e4e7ed;

  --rise-color: #e63946;
  --fall-color: #2a9d5c;
  --success-color: #2a9d5c;
  --warning-color: #f59e0b;

  --shadow-sm: 0 1px 2px rgba(0,0,0,0.04);
  --shadow: 0 2px 12px rgba(0,0,0,0.08);
  --shadow-md: 0 4px 16px rgba(0,0,0,0.1);
  --shadow-lg: 0 8px 32px rgba(0,0,0,0.12);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Fira Sans', -apple-system, BlinkMacSystemFont, sans-serif;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}

body ::selection {
  background: var(--color-primary);
  color: #fff;
}

#app {
  min-height: 100vh;
}

.main-nav {
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-light);
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(8px);
}

.nav-container {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  padding: 0 24px;
  height: 64px;
  gap: 32px;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.brand-mark {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-primary);
  transition: transform 0.3s ease;
}

.nav-brand:hover .brand-mark {
  transform: rotate(30deg);
}

.brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.brand-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.3px;
}

.brand-tag {
  font-size: 11px;
  font-weight: 500;
  color: var(--color-primary);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.nav-links {
  display: flex;
  gap: 4px;
  flex: 1;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 8px;
  text-decoration: none;
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 14px;
  transition: all 0.2s ease;
  position: relative;
  border: none;
  background: none;
  cursor: pointer;
  font-family: inherit;
}

.nav-link::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 50%;
  transform: translateX(-50%) scaleX(0);
  width: 24px;
  height: 2px;
  background: var(--color-primary);
  border-radius: 1px;
  transition: transform 0.2s ease;
}

.link-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.6;
  transition: opacity 0.2s ease;
}

.nav-link:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}

.nav-link:hover .link-icon {
  opacity: 0.8;
}

.nav-link.router-link-active {
  color: var(--color-primary);
  background: var(--color-primary-dim);
}

.nav-link.router-link-active::after {
  transform: translateX(-50%) scaleX(1);
}

.nav-link.router-link-active .link-icon {
  opacity: 1;
}

.nav-actions {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.user-dropdown-trigger {
  cursor: pointer;
}

.user-dropdown-trigger .link-icon {
  opacity: 0.6;
}

.user-dropdown-trigger:hover .link-icon {
  opacity: 0.8;
}

.el-card {
  --el-card-bg-color: var(--bg-card);
  --el-card-border-color: var(--border-light);
  border-radius: 16px;
  box-shadow: var(--shadow);
  border: 1px solid var(--border-light);
  transition: box-shadow 0.3s ease;
}

.el-card:hover {
  box-shadow: var(--shadow-md);
}

.el-table {
  --el-table-bg-color: var(--bg-card);
  --el-table-tr-bg-color: var(--bg-card);
  --el-table-header-bg-color: var(--bg-primary);
  --el-table-row-hover-bg-color: var(--bg-hover);
  --el-table-border-color: var(--border-light);
  --el-table-text-color: var(--text-primary);
  --el-table-header-text-color: var(--text-secondary);
}

.el-table th.el-table__cell {
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.el-input__wrapper {
  background-color: var(--bg-card);
  border-color: var(--border-color);
  box-shadow: none;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.el-input__wrapper:hover {
  border-color: var(--color-primary-light);
}

.el-input__wrapper.is-focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-dim);
}

.el-input__inner {
  color: var(--text-primary);
}

.el-select .el-input__wrapper {
  background-color: var(--bg-card);
  border-color: var(--border-color);
  box-shadow: none;
  border-radius: 8px;
}

.el-select__wrapper {
  background-color: var(--bg-card);
  border-color: var(--border-color);
  box-shadow: none;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.el-select__wrapper:hover {
  border-color: var(--color-primary-light);
}

.el-select__wrapper.is-focused {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-dim);
}

.el-select__wrapper .el-select__caret {
  color: var(--text-secondary);
}

.el-select-dropdown {
  background-color: var(--bg-card);
  border-color: var(--border-light);
  border-radius: 12px;
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}

.el-select-dropdown__item {
  color: var(--text-primary);
  border-radius: 6px;
  margin: 4px 8px;
}

.el-select-dropdown__item.hover,
.el-select-dropdown__item:hover {
  background-color: var(--color-primary-dim);
}

.el-select-dropdown__item.is-selected {
  background-color: var(--color-primary-dim);
  color: var(--color-primary);
  font-weight: 600;
}

.el-dialog {
  --el-dialog-bg-color: var(--bg-card);
  --el-dialog-border-color: var(--border-light);
  border-radius: 20px;
  overflow: hidden;
}

.el-dialog__header {
  padding: 20px 24px 0;
}

.el-dialog__title {
  font-family: 'Fira Sans', sans-serif;
  font-weight: 600;
  font-size: 18px;
  color: var(--text-primary);
}

.el-dialog__body {
  padding: 24px;
}

.el-button {
  border-color: var(--border-color);
  font-family: 'Fira Sans', sans-serif;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.el-button:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

.el-button--primary {
  --el-button-bg-color: var(--color-primary);
  --el-button-border-color: var(--color-primary);
  --el-button-hover-bg-color: var(--color-primary-dark);
  --el-button-hover-border-color: var(--color-primary-dark);
  --el-button-active-bg-color: var(--color-primary-dark);
}

.el-tabs__item {
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 14px;
  padding: 0 20px;
  height: 44px;
}

.el-tabs__item:hover {
  color: var(--color-primary);
}

.el-tabs__item.is-active {
  color: var(--color-primary);
}

.el-tabs__active-bar {
  background-color: var(--color-primary);
  height: 3px;
  border-radius: 2px;
}

.el-tabs__nav-wrap::after {
  background-color: var(--border-light);
  height: 1px;
}

::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--color-primary-light);
}

/* Feedback dialog */
.feedback-dialog .el-dialog__body {
  padding: 20px 24px 16px;
}

.feedback-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: var(--color-primary-pale);
  border-radius: 10px;
  color: var(--color-primary-dark);
  font-size: 13px;
  margin-bottom: 16px;
}

.feedback-tip svg {
  flex-shrink: 0;
  color: var(--color-primary);
}

.feedback-textarea {
  margin-bottom: 4px;
}

.feedback-textarea .el-textarea__inner {
  border-radius: 10px;
  resize: none;
  font-size: 14px;
  line-height: 1.6;
}

.feedback-char-count {
  text-align: right;
  font-size: 12px;
  color: var(--text-muted);
  padding: 0 4px;
}

.btn-cancel {
  background: var(--bg-primary);
  border-color: var(--border-color);
  color: var(--text-secondary);
}

.btn-cancel:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.btn-submit-feedback {
  background: var(--color-primary);
  border-color: var(--color-primary);
  font-weight: 500;
}

.btn-submit-feedback:hover {
  background: var(--color-primary-dark);
  border-color: var(--color-primary-dark);
}

/* Update log dialog */
.logs-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px;
  color: var(--text-muted);
}

.logs-empty {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
}

.logs-list {
  max-height: 400px;
  overflow-y: auto;
}

.log-item {
  display: flex;
  gap: 16px;
  padding: 14px 0;
  border-bottom: 1px solid var(--border-light);
}

.log-item:last-child {
  border-bottom: none;
}

.log-date {
  flex-shrink: 0;
  width: 90px;
  font-size: 13px;
  color: var(--color-primary);
  font-weight: 500;
}

.log-content {
  flex: 1;
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.6;
}

.el-pagination {
  --el-pagination-bg-color: var(--bg-card);
  --el-pagination-text-color: var(--text-secondary);
  --el-pagination-button-bg-color: var(--bg-card);
  --el-pagination-button-color: var(--text-secondary);
  --el-pagination-button-disabled-bg-color: var(--bg-hover);
}

.el-pagination .el-pager li {
  border-radius: 8px;
  margin: 0 2px;
}

.el-pagination .el-pager li:hover {
  color: var(--color-primary);
}

.el-pagination .el-pager li.is-active {
  background: var(--color-primary);
  color: #fff;
}

.el-date-editor .el-input__wrapper {
  background-color: var(--bg-card);
  border-radius: 8px;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.animate-in {
  opacity: 0;
  animation: fadeInUp 0.5s ease-out forwards;
}

.animate-fade {
  animation: fadeIn 0.3s ease-out forwards;
}
</style>
