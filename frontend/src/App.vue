<template>
  <div id="app">
    <!-- Subtle background pattern -->
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

          <router-link to="/manage" class="nav-link">
            <span class="link-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
                <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
                <line x1="12" y1="22.08" x2="12" y2="12"/>
              </svg>
            </span>
            <span class="link-text">产品管理</span>
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

          <router-link to="/alerts" class="nav-link">
            <span class="link-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
              </svg>
            </span>
            <span class="link-text">价格预警</span>
          </router-link>
        </div>

        <div class="nav-actions">
          <div class="nav-divider"></div>
          <el-button type="primary" size="small" class="nav-refresh-btn" @click="triggerUpdate">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="23 4 23 10 17 10"/>
              <polyline points="1 20 1 14 7 14"/>
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
            </svg>
            刷新数据
          </el-button>
        </div>
      </div>
    </nav>

    <!-- 数据新鲜度提示弹窗 -->
    <el-dialog
      v-model="showFreshnessDialog"
      title="数据更新提醒"
      width="420px"
      :close-on-click-modal="updating ? false : true"
      :show-close="!updating"
      class="freshness-dialog"
    >
      <div v-if="updating" class="freshness-loading">
        <div class="loading-spinner">
          <svg width="48" height="48" viewBox="0 0 48 48">
            <circle cx="24" cy="24" r="20" stroke="currentColor" stroke-width="3" fill="none" stroke-dasharray="80 40"/>
          </svg>
        </div>
        <p class="loading-title">正在抓取数据</p>
        <p class="loading-tip">抓取完成后可正常操作系统</p>
      </div>
      <div v-else-if="freshnessData.any_needs_update" class="freshness-warning">
        <div class="warning-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
        </div>
        <p class="warning-title">以下数据源需要更新</p>
        <ul class="warning-list">
          <li v-for="s in freshnessData.sources" :key="s.source" :class="{ 'needs-update': s.needs_update }">
            <span class="source-name">{{ s.source }}</span>
            <span class="source-status">{{ s.message }}</span>
          </li>
        </ul>
      </div>
      <div v-else class="freshness-ok">
        <div class="ok-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
        </div>
        <p class="ok-text">所有数据已是最新</p>
      </div>
      <template #footer>
        <el-button v-if="!updating" @click="handleLater" class="btn-later">稍后</el-button>
        <el-button v-if="!updating && freshnessData.any_needs_update" type="primary" @click="triggerUpdate" class="btn-update">
          立即更新
        </el-button>
      </template>
    </el-dialog>

    <router-view />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { scraperApi } from './api/price'
import { ElMessage } from 'element-plus'

const showFreshnessDialog = ref(false)
const freshnessData = ref({ any_needs_update: false, sources: [] })
const updating = ref(false)

const FRESHNESS_CACHE_KEY = 'procurement_freshness_check_ts'
const FRESHNESS_CACHE_DURATION = 60 * 60 * 1000 // 1小时

async function checkFreshness() {
  const cached = localStorage.getItem(FRESHNESS_CACHE_KEY)
  if (cached && Date.now() - parseInt(cached) < FRESHNESS_CACHE_DURATION) {
    return
  }

  try {
    const res = await scraperApi.checkFreshness()
    freshnessData.value = res.data
    if (res.data.any_needs_update) {
      localStorage.setItem(FRESHNESS_CACHE_KEY, Date.now().toString())
      showFreshnessDialog.value = true
    }
  } catch (e) {
    console.error('Failed to check freshness', e)
  }
}

function handleLater() {
  showFreshnessDialog.value = false
}

async function triggerUpdate() {
  updating.value = true
  try {
    const res = await scraperApi.runScraper('shengyishe')
    if (res.data?.status === 'skipped') {
      ElMessage.info(res.data.message || '请稍后再试')
      updating.value = false
      showFreshnessDialog.value = false
      return
    }
    ElMessage.success('数据更新成功')
    localStorage.removeItem(FRESHNESS_CACHE_KEY)
    window.location.reload()
  } catch (e) {
    console.error('Update failed', e)
    ElMessage.error('数据更新失败：' + (e?.response?.data?.detail || e.message || '请稍后重试'))
    updating.value = false
    showFreshnessDialog.value = false
  }
}

onMounted(() => {
  checkFreshness()
})
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Fira+Sans:wght@300;400;500;600;700&family=Fira+Code:wght@400;500;600&display=swap');

:root {
  /* Primary - Cyan */
  --color-primary: #0077cc;
  --color-primary-light: #00a8e8;
  --color-primary-pale: #e6f4fa;
  --color-primary-dark: #005fa3;
  --color-primary-dim: rgba(0, 119, 204, 0.1);
  --color-primary-glow: rgba(0, 119, 204, 0.15);

  /* Background */
  --bg-primary: #f5f7fa;
  --bg-secondary: #ffffff;
  --bg-card: #ffffff;
  --bg-hover: #f0f2f5;
  --bg-elevated: #fafbfc;

  /* Text */
  --text-primary: #1a1a2e;
  --text-secondary: #5a6178;
  --text-muted: #9ca3af;

  /* Border */
  --border-color: #e4e7ed;
  --border-light: #e4e7ed;

  /* Semantic */
  --rise-color: #e63946;
  --fall-color: #2a9d5c;
  --warning-color: #f59e0b;

  /* Shadow */
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

/* Navigation */
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
  gap: 16px;
  flex-shrink: 0;
}

.nav-divider {
  width: 1px;
  height: 24px;
  background: var(--border-color);
}

.nav-refresh-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px !important;
  border-radius: 8px !important;
  font-weight: 500 !important;
  font-size: 13px !important;
  transition: all 0.2s ease !important;
}

.nav-refresh-btn:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

/* Global card styles */
.el-card {
  --el-card-bg-color: var(--bg-card) !important;
  --el-card-border-color: var(--border-light) !important;
  border-radius: 16px !important;
  box-shadow: var(--shadow) !important;
  border: 1px solid var(--border-light) !important;
  transition: box-shadow 0.3s ease !important;
}

.el-card:hover {
  box-shadow: var(--shadow-md) !important;
}

/* Element Plus overrides */
.el-table {
  --el-table-bg-color: var(--bg-card) !important;
  --el-table-tr-bg-color: var(--bg-card) !important;
  --el-table-header-bg-color: var(--bg-primary) !important;
  --el-table-row-hover-bg-color: var(--bg-hover) !important;
  --el-table-border-color: var(--border-light) !important;
  --el-table-text-color: var(--text-primary) !important;
  --el-table-header-text-color: var(--text-secondary) !important;
}

.el-table th.el-table__cell {
  font-weight: 600 !important;
  font-size: 12px !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.el-input__wrapper {
  background-color: var(--bg-card) !important;
  border-color: var(--border-color) !important;
  box-shadow: none !important;
  border-radius: 8px !important;
  transition: all 0.2s ease !important;
}

.el-input__wrapper:hover {
  border-color: var(--color-primary-light) !important;
}

.el-input__wrapper.is-focus {
  border-color: var(--color-primary) !important;
  box-shadow: 0 0 0 3px var(--color-primary-dim) !important;
}

.el-input__inner {
  color: var(--text-primary) !important;
}

.el-select .el-input__wrapper {
  background-color: var(--bg-card) !important;
  border-color: var(--border-color) !important;
  box-shadow: none !important;
  border-radius: 8px !important;
}

.el-select__wrapper {
  background-color: var(--bg-card) !important;
  border-color: var(--border-color) !important;
  box-shadow: none !important;
  border-radius: 8px !important;
  transition: all 0.2s ease !important;
}

.el-select__wrapper:hover {
  border-color: var(--color-primary-light) !important;
}

.el-select__wrapper.is-focused {
  border-color: var(--color-primary) !important;
  box-shadow: 0 0 0 3px var(--color-primary-dim) !important;
}

.el-select__wrapper .el-select__caret {
  color: var(--text-secondary) !important;
}

.el-select-dropdown {
  background-color: var(--bg-card) !important;
  border-color: var(--border-light) !important;
  border-radius: 12px !important;
  box-shadow: var(--shadow-lg) !important;
  overflow: hidden;
}

.el-select-dropdown__item {
  color: var(--text-primary) !important;
  border-radius: 6px !important;
  margin: 4px 8px !important;
}

.el-select-dropdown__item.hover,
.el-select-dropdown__item:hover {
  background-color: var(--color-primary-dim) !important;
}

.el-select-dropdown__item.is-selected {
  background-color: var(--color-primary-dim) !important;
  color: var(--color-primary) !important;
  font-weight: 600 !important;
}

.el-dialog {
  --el-dialog-bg-color: var(--bg-card) !important;
  --el-dialog-border-color: var(--border-light) !important;
  border-radius: 20px !important;
  overflow: hidden;
}

.el-dialog__header {
  padding: 20px 24px 0 !important;
}

.el-dialog__title {
  font-family: 'Fira Sans', sans-serif !important;
  font-weight: 600 !important;
  font-size: 18px !important;
  color: var(--text-primary) !important;
}

.el-dialog__body {
  padding: 24px !important;
}

.el-button {
  border-color: var(--border-color) !important;
  font-family: 'Fira Sans', sans-serif !important;
  border-radius: 8px !important;
  font-weight: 500 !important;
  transition: all 0.2s ease !important;
}

.el-button:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm) !important;
}

.el-button--primary {
  --el-button-bg-color: var(--color-primary) !important;
  --el-button-border-color: var(--color-primary) !important;
  --el-button-hover-bg-color: var(--color-primary-dark) !important;
  --el-button-hover-border-color: var(--color-primary-dark) !important;
  --el-button-active-bg-color: var(--color-primary-dark) !important;
}

.el-tabs__item {
  color: var(--text-secondary) !important;
  font-weight: 500 !important;
  font-size: 14px !important;
  padding: 0 20px !important;
  height: 44px !important;
}

.el-tabs__item:hover {
  color: var(--color-primary) !important;
}

.el-tabs__item.is-active {
  color: var(--color-primary) !important;
}

.el-tabs__active-bar {
  background-color: var(--color-primary) !important;
  height: 3px !important;
  border-radius: 2px !important;
}

.el-tabs__nav-wrap::after {
  background-color: var(--border-light) !important;
  height: 1px !important;
}

/* Custom scrollbar */
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

/* Dialog styles */
.freshness-loading {
  text-align: center;
  padding: 32px 0;
}

.loading-spinner {
  color: var(--color-primary);
  margin-bottom: 20px;
}

.loading-spinner svg {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.loading-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.loading-tip {
  font-size: 13px;
  color: var(--text-muted);
}

.freshness-warning {
  text-align: center;
}

.warning-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--color-primary-dim);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
}

.warning-title {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 16px;
}

.warning-list {
  list-style: none;
  text-align: left;
  background: var(--bg-primary);
  border-radius: 12px;
  padding: 12px 16px;
}

.warning-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--border-light);
}

.warning-list li:last-child {
  border-bottom: none;
}

.warning-list li.needs-update .source-status {
  color: var(--rise-color);
  font-weight: 500;
}

.source-name {
  font-weight: 500;
  color: var(--text-primary);
}

.source-status {
  font-size: 13px;
  color: var(--text-secondary);
}

.freshness-ok {
  text-align: center;
  padding: 24px 0;
}

.ok-icon {
  color: var(--fall-color);
  margin-bottom: 16px;
}

.ok-text {
  font-size: 16px;
  font-weight: 500;
  color: var(--fall-color);
}

.btn-later {
  background: var(--bg-primary) !important;
  border-color: var(--border-color) !important;
  color: var(--text-secondary) !important;
}

.btn-later:hover {
  background: var(--bg-hover) !important;
  color: var(--text-primary) !important;
}

.btn-update {
  background: var(--color-primary) !important;
  border-color: var(--color-primary) !important;
  font-weight: 600 !important;
}

/* Pagination */
.el-pagination {
  --el-pagination-bg-color: var(--bg-card);
  --el-pagination-text-color: var(--text-secondary);
  --el-pagination-button-bg-color: var(--bg-card);
  --el-pagination-button-color: var(--text-secondary);
  --el-pagination-button-disabled-bg-color: var(--bg-hover);
}

.el-pagination .el-pager li {
  border-radius: 8px !important;
  margin: 0 2px;
}

.el-pagination .el-pager li:hover {
  color: var(--color-primary) !important;
}

.el-pagination .el-pager li.is-active {
  background: var(--color-primary) !important;
  color: #fff !important;
}

.el-date-editor .el-input__wrapper {
  background-color: var(--bg-card) !important;
  border-radius: 8px !important;
}

/* Animation keyframes */
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