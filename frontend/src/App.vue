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
      :close-on-click-modal="false"
      :show-close="false"
    >
      <div v-if="freshnessData.any_needs_update" class="freshness-warning">
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
        <el-button @click="showFreshnessDialog = false">稍后</el-button>
        <el-button v-if="freshnessData.any_needs_update" type="primary" @click="triggerUpdate">
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

const showFreshnessDialog = ref(false)
const freshnessData = ref({ any_needs_update: false, sources: [] })

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

async function triggerUpdate() {
  showFreshnessDialog.value = false
  try {
    await scraperApi.runScraper('shengyishe')
    window.location.reload()
  } catch (e) {
    console.error('Update failed', e)
  }
}

onMounted(() => {
  checkFreshness()
})
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

:root {
  --bg-primary: #0f1419;
  --bg-secondary: #1a1f26;
  --bg-card: #21262d;
  --bg-hover: #2d333b;
  --accent-cyan: #00d4ff;
  --accent-cyan-dim: rgba(0, 212, 255, 0.15);
  --rise-color: #ff6b6b;
  --fall-color: #00c48c;
  --text-primary: #e8eaed;
  --text-secondary: #8b949e;
  --text-muted: #545d68;
  --border-color: #30363d;
  --shadow: 0 8px 24px rgba(0,0,0,0.4);
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
  background: linear-gradient(135deg, var(--text-primary), var(--accent-cyan));
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

/* Element Plus overrides for dark theme */
.el-table {
  --el-table-bg-color: var(--bg-card) !important;
  --el-table-tr-bg-color: var(--bg-card) !important;
  --el-table-header-bg-color: var(--bg-secondary) !important;
  --el-table-row-hover-bg-color: var(--bg-hover) !important;
  --el-table-border-color: var(--border-color) !important;
  --el-table-text-color: var(--text-primary) !important;
  --el-table-header-text-color: var(--text-secondary) !important;
}

.el-input__wrapper {
  background-color: var(--bg-secondary) !important;
  border-color: var(--border-color) !important;
  box-shadow: none !important;
}

.el-input__inner {
  color: var(--text-primary) !important;
}

.el-select .el-input__wrapper {
  background-color: var(--bg-secondary) !important;
  border-color: var(--border-color) !important;
  box-shadow: none !important;
}

.el-select .el-input__wrapper .el-input__inner {
  color: var(--text-primary) !important;
}

.el-select__wrapper {
  background-color: var(--bg-secondary) !important;
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
  --el-button-hover-bg-color: #00b8e6 !important;
  --el-button-hover-border-color: #00b8e6 !important;
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
  background: var(--bg-secondary);
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