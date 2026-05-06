<template>
  <div id="app">
    <nav class="main-nav">
      <div class="nav-brand">
        <span class="brand-icon">◈</span>
        <span class="brand-text">Procurement</span>
      </div>
      <div class="nav-links">
        <router-link to="/" class="nav-link">
          <span class="link-icon">◎</span>
          数据看板
        </router-link>
        <router-link to="/compare" class="nav-link">
          <span class="link-icon">⬡</span>
          产品对比
        </router-link>
        <router-link to="/manage" class="nav-link">
          <span class="link-icon">◧</span>
          产品管理
        </router-link>
        <router-link to="/reports" class="nav-link">
          <span class="link-icon">◫</span>
          报表中心
        </router-link>
        <router-link to="/alerts" class="nav-link">
          <span class="link-icon">⚠</span>
          价格预警
        </router-link>
      </div>
    </nav>

    <!-- 数据新鲜度提示弹窗 -->
    <el-dialog
      v-model="showFreshnessDialog"
      title="数据更新提醒"
      width="480px"
      :close-on-click-modal="updating ? false : true"
      :show-close="!updating"
    >
      <div v-if="updating" class="freshness-loading">
        <el-icon class="loading-icon is-loading"><Loading /></el-icon>
        <p>正在抓取数据，请稍候...</p>
        <p class="loading-tip">抓取完成后可正常操作系统</p>
      </div>
      <div v-else-if="freshnessData.any_needs_update" class="freshness-warning">
        <p>以下数据源需要更新：</p>
        <ul>
          <li v-for="s in freshnessData.sources" :key="s.source" :class="{ 'needs-update': s.needs_update }">
            <strong>{{ s.source }}</strong>: {{ s.message }}
          </li>
        </ul>
      </div>
      <div v-else class="freshness-ok">
        <p>所有数据已是最新</p>
      </div>
      <template #footer>
        <el-button v-if="!updating" @click="handleLater">稍后</el-button>
        <el-button v-if="!updating && freshnessData.any_needs_update" type="primary" @click="triggerUpdate">
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
import { Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const showFreshnessDialog = ref(false)
const freshnessData = ref({ any_needs_update: false, sources: [] })
const updating = ref(false)

async function checkFreshness() {
  try {
    const res = await scraperApi.checkFreshness()
    freshnessData.value = res.data
    if (res.data.any_needs_update) {
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
    await scraperApi.runScraper('shengyishe')
    ElMessage.success('数据更新成功')
    // 刷新页面以显示新数据
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
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

:root {
  --bg-primary: #f5f7fa;
  --bg-secondary: #ffffff;
  --bg-card: #ffffff;
  --bg-hover: #f0f2f5;
  --bg-elevated: #fafbfc;
  --accent-cyan: #0077cc;
  --accent-cyan-dim: rgba(0, 119, 204, 0.1);
  --rise-color: #e63946;
  --fall-color: #2a9d5c;
  --text-primary: #1a1a2e;
  --text-secondary: #5a6178;
  --text-muted: #9ca3af;
  --border-color: #e4e7ed;
  --shadow: 0 2px 12px rgba(0,0,0,0.08);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  line-height: 1.6;
}

body ::selection {
  background: var(--accent-cyan);
  color: #fff;
}

#app {
  min-height: 100vh;
}

.main-nav {
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  padding: 0 32px;
  height: 64px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-right: 48px;
}

.brand-icon {
  font-size: 24px;
  color: var(--accent-cyan);
}

.brand-text {
  font-family: 'Outfit', sans-serif;
  font-weight: 700;
  font-size: 18px;
  letter-spacing: -0.5px;
  background: linear-gradient(135deg, var(--accent-cyan), #005fa3);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.nav-links {
  display: flex;
  gap: 4px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  border-radius: 8px;
  text-decoration: none;
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 14px;
  transition: all 0.2s ease;
}

.link-icon {
  font-size: 16px;
  opacity: 0.7;
}

.nav-link:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}

.nav-link.router-link-active {
  color: var(--accent-cyan);
  background: var(--accent-cyan-dim);
}

.nav-link.router-link-active .link-icon {
  opacity: 1;
}

/* Global card styles */
.el-card {
  --el-card-bg-color: var(--bg-card) !important;
  --el-card-border-color: var(--border-color) !important;
  border-radius: 12px !important;
  box-shadow: var(--shadow) !important;
}

/* Element Plus overrides for light theme */
.el-table {
  --el-table-bg-color: var(--bg-card) !important;
  --el-table-tr-bg-color: var(--bg-card) !important;
  --el-table-header-bg-color: var(--bg-primary) !important;
  --el-table-row-hover-bg-color: var(--bg-hover) !important;
  --el-table-border-color: var(--border-color) !important;
  --el-table-text-color: var(--text-primary) !important;
  --el-table-header-text-color: var(--text-secondary) !important;
}

.el-input__wrapper {
  background-color: var(--bg-card) !important;
  border-color: var(--border-color) !important;
  box-shadow: none !important;
}

.el-input__inner {
  color: var(--text-primary) !important;
}

.el-select .el-input__wrapper {
  background-color: var(--bg-card) !important;
  border-color: var(--border-color) !important;
  box-shadow: none !important;
}

.el-select .el-input__wrapper .el-input__inner {
  color: var(--text-primary) !important;
}

.el-select__wrapper {
  background-color: var(--bg-card) !important;
  border-color: var(--border-color) !important;
  box-shadow: none !important;
}

.el-select__wrapper .el-select__caret {
  color: var(--text-secondary) !important;
}

.el-select-dropdown {
  background-color: var(--bg-card) !important;
  border-color: var(--border-color) !important;
}

.el-select-dropdown__item {
  color: var(--text-primary) !important;
}

.el-select-dropdown__item.hover,
.el-select-dropdown__item:hover {
  background-color: var(--bg-hover) !important;
}

.el-dialog {
  --el-dialog-bg-color: var(--bg-card) !important;
  --el-dialog-border-color: var(--border-color) !important;
  border-radius: 16px !important;
}

.el-button {
  border-color: var(--border-color) !important;
  font-family: 'IBM Plex Sans', sans-serif !important;
}

.el-button--primary {
  --el-button-bg-color: var(--accent-cyan) !important;
  --el-button-border-color: var(--accent-cyan) !important;
  --el-button-hover-bg-color: #005fa3 !important;
  --el-button-hover-border-color: #005fa3 !important;
}

.el-tabs__item {
  color: var(--text-secondary) !important;
}

.el-tabs__item.is-active {
  color: var(--accent-cyan) !important;
}

.el-tabs__active-bar {
  background-color: var(--accent-cyan) !important;
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--bg-primary);
}

::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--text-muted);
}

.freshness-warning ul {
  margin: 12px 0 0 20px;
  line-height: 1.8;
}

.freshness-warning li {
  color: var(--text-secondary);
}

.freshness-warning li.needs-update {
  color: var(--rise-color);
}

.freshness-ok p {
  color: var(--fall-color);
  font-size: 16px;
}

.freshness-loading {
  text-align: center;
  padding: 20px 0;
}

.freshness-loading .loading-icon {
  font-size: 48px;
  color: var(--accent-cyan);
  margin-bottom: 16px;
}

.freshness-loading p {
  color: var(--text-primary);
  font-size: 16px;
  margin: 8px 0;
}

.freshness-loading .loading-tip {
  color: var(--text-muted);
  font-size: 14px;
}

.el-pagination {
  --el-pagination-bg-color: var(--bg-card);
  --el-pagination-text-color: var(--text-secondary);
  --el-pagination-button-bg-color: var(--bg-card);
  --el-pagination-button-color: var(--text-secondary);
  --el-pagination-button-disabled-bg-color: var(--bg-hover);
}

.el-date-editor .el-input__wrapper {
  background-color: var(--bg-card) !important;
}
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-in {
  animation: fadeInUp 0.4s ease-out forwards;
}
</style>