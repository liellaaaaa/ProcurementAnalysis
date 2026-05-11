<template>
  <div class="report-view">
    <div class="page-container">
      <header class="page-header">
      </header>

      <el-card class="filter-card animate-in">
        <el-form :inline="true" class="filter-form">
          <el-form-item label="报表类型">
            <el-select v-model="reportType" style="width: 120px">
              <el-option label="周报" value="weekly">
                <span class="option-label">◫ 周报</span>
              </el-option>
              <el-option label="月报" value="monthly">
                <span class="option-label">◧ 月报</span>
              </el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="月份" v-if="reportType === 'monthly'">
            <el-date-picker v-model="month" type="month" value-format="YYYY-MM" placeholder="选择月份" />
          </el-form-item>
          <el-form-item label="开始日期" v-if="reportType === 'weekly'">
            <el-date-picker v-model="startDate" type="date" value-format="YYYY-MM-DD" placeholder="选择开始日期" />
          </el-form-item>
          <el-form-item label="结束日期" v-if="reportType === 'weekly'">
            <el-date-picker v-model="endDate" type="date" value-format="YYYY-MM-DD" placeholder="选择结束日期" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="loadStats" class="query-btn">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8"/>
                <line x1="21" y1="21" x2="16.65" y2="16.65"/>
              </svg>
              查询数据
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <div class="stats-grid">
        <div class="stat-card" v-for="(stat, index) in statCards" :key="stat.label" :style="{ animationDelay: `${index * 0.08}s` }">
          <div class="stat-icon" :style="{ background: stat.bgColor }">
            <span v-html="stat.icon"></span>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stat.value }}</div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
        </div>
      </div>

      <el-card class="download-card animate-in" style="animation-delay: 0.2s">
        <template #header>
          <div class="card-header">
            <div class="header-title">
              <div class="title-icon-wrapper">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                </svg>
              </div>
              <span>报告导出</span>
            </div>
          </div>
        </template>
        <div class="download-buttons">
          <button class="download-btn pdf" @click="downloadPdf">
            <div class="btn-icon-wrapper pdf">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
              </svg>
            </div>
            <span class="btn-text">下载 PDF 报告</span>
            <span class="btn-desc">适合打印与存档</span>
          </button>
          <button class="download-btn excel" @click="downloadExcel">
            <div class="btn-icon-wrapper excel">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                <line x1="3" y1="9" x2="21" y2="9"/>
                <line x1="3" y1="15" x2="21" y2="15"/>
                <line x1="9" y1="3" x2="9" y2="21"/>
                <line x1="15" y1="3" x2="15" y2="21"/>
              </svg>
            </div>
            <span class="btn-text">下载 Excel 报表</span>
            <span class="btn-desc">便于数据分析处理</span>
          </button>
        </div>
      </el-card>

      <div class="bottom-grid" v-if="rankingData.rising.length">
        <el-card class="ranking-card animate-in" style="animation-delay: 0.3s" v-if="rankingData.rising.length">
          <template #header>
            <div class="card-header">
              <div class="header-title">
                <div class="title-icon-wrapper">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="20" x2="18" y2="10"/>
                    <line x1="12" y1="20" x2="12" y2="4"/>
                    <line x1="6" y1="20" x2="6" y2="14"/>
                  </svg>
                </div>
                <span>较昨日涨跌排行</span>
              </div>
            </div>
          </template>
          <el-tabs>
            <el-tab-pane label="涨幅榜">
              <div class="ranking-list">
                <div v-for="(item, index) in rankingData.rising" :key="index" class="ranking-item rising">
                  <span class="rank-num">{{ index + 1 }}</span>
                  <span class="rank-name">{{ item.product_name }}</span>
                  <span class="rank-price">¥{{ item.latest_price?.toLocaleString() }}</span>
                  <span class="rank-change rise">+{{ item.change_percent }}%</span>
                </div>
              </div>
            </el-tab-pane>
            <el-tab-pane label="跌幅榜">
              <div class="ranking-list">
                <div v-for="(item, index) in rankingData.falling" :key="index" class="ranking-item falling">
                  <span class="rank-num">{{ index + 1 }}</span>
                  <span class="rank-name">{{ item.product_name }}</span>
                  <span class="rank-price">¥{{ item.latest_price?.toLocaleString() }}</span>
                  <span class="rank-change fall">{{ item.change_percent }}%</span>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { reportApi } from '../api/price'

const reportType = ref('weekly')
const month = ref('')
const startDate = ref('')
const endDate = ref('')
const stats = ref({})
const rankingData = ref({ rising: [], falling: [] })

const statCards = ref([
  { icon: '◈', label: '产品数量', value: 0, bgColor: 'rgba(0, 212, 255, 0.15)' },
  { icon: '◧', label: '价格记录', value: 0, bgColor: 'rgba(255, 107, 107, 0.15)' },
  { icon: '◎', label: '最高价', value: '-', bgColor: 'rgba(0, 196, 140, 0.15)' },
  { icon: '◫', label: '平均价', value: '-', bgColor: 'rgba(255, 217, 61, 0.15)' }
])

onMounted(() => {
  loadStats()
})

function getEffectiveDates() {
  let s = startDate.value
  let e = endDate.value
  if (reportType.value === 'monthly' && month.value) {
    const [year, mon] = month.value.split('-')
    const lastDay = new Date(year, mon, 0).getDate()
    s = `${year}-${mon}-01`
    e = `${year}-${mon}-${String(lastDay).padStart(2, '0')}`
  }
  return { startDate: s || null, endDate: e || null }
}

async function loadStats() {
  try {
    let statsRes
    if (reportType.value === 'weekly') {
      statsRes = await reportApi.getWeeklyStats()
    } else {
      statsRes = await reportApi.getMonthlyStats(month.value)
    }

    const products = statsRes.data.products || []
    if (products.length > 0) {
      stats.value = {
        product_count: products.length,
        record_count: products.reduce((sum, p) => sum + p.record_count, 0),
        max_price: Math.max(...products.map(p => p.max_price)),
        avg_price: products.reduce((sum, p) => sum + p.avg_price * p.record_count, 0) / products.reduce((sum, p) => sum + p.record_count, 0)
      }
      statCards.value[0].value = products.length
      statCards.value[1].value = products.reduce((sum, p) => sum + p.record_count, 0)
      statCards.value[2].value = `¥${Math.max(...products.map(p => p.max_price)).toLocaleString()}`
      statCards.value[3].value = `¥${Math.round(stats.value.avg_price).toLocaleString()}`
    } else {
      statCards.value.forEach(s => s.value = 0)
    }

    const rankingRes = await reportApi.getRanking(7)
    rankingData.value = rankingRes.data
  } catch (e) {
    ElMessage.error('加载统计数据失败')
  }
}

async function downloadPdf() {
  try {
    const { startDate: s, endDate: e } = getEffectiveDates()
    const res = await reportApi.downloadPdf(reportType.value, s, e)
    const blob = new Blob([res.data], { type: 'application/pdf' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `price_${reportType.value}_${new Date().toISOString().slice(0, 10)}.pdf`
    a.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('PDF 下载成功')
  } catch (e) {
    ElMessage.error('PDF 下载失败')
  }
}

async function downloadExcel() {
  try {
    const { startDate: s, endDate: e } = getEffectiveDates()
    const res = await reportApi.downloadExcel(reportType.value, s, e)
    const blob = new Blob([res.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `price_${reportType.value}_${new Date().toISOString().slice(0, 10)}.xlsx`
    a.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('Excel 下载成功')
  } catch (e) {
    ElMessage.error('Excel 下载失败')
  }
}
</script>

<style scoped>
.report-view {
  padding: 24px;
  min-height: 100vh;
}

.page-container {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.header-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page-title {
  font-family: 'Fira Sans', sans-serif;
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.page-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

.filter-card {
  margin-bottom: 24px;
  border-radius: 16px !important;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: flex-end;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.option-label {
  font-size: 13px;
}

.query-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px !important;
  border-radius: 8px !important;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  opacity: 0;
  animation: fadeInUp 0.5s ease-out forwards;
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}

.stat-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: var(--color-primary);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-family: 'Fira Sans', sans-serif;
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.stat-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 2px;
}

.download-card {
  margin-bottom: 24px;
  border-radius: 16px !important;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: 'Fira Sans', sans-serif;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.title-icon-wrapper {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: var(--color-primary-dim);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.download-buttons {
  display: flex;
  gap: 20px;
  justify-content: center;
  padding: 24px 0;
}

.download-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 32px 56px;
  border: 1px solid var(--border-color);
  border-radius: 16px;
  background: var(--bg-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.download-btn:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
}

.download-btn.pdf:hover {
  border-color: var(--rise-color);
}

.download-btn.pdf .btn-icon-wrapper {
  background: rgba(230, 57, 70, 0.12);
  color: var(--rise-color);
}

.download-btn.excel:hover {
  border-color: var(--fall-color);
}

.download-btn.excel .btn-icon-wrapper {
  background: rgba(42, 157, 92, 0.12);
  color: var(--fall-color);
}

.btn-icon-wrapper {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.btn-text {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.btn-desc {
  font-size: 12px;
  color: var(--text-muted);
}

.bottom-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.ranking-card {
  border-radius: 16px !important;
}

.ranking-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ranking-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: var(--bg-primary);
  border-radius: 8px;
  transition: transform 0.2s ease;
}

.ranking-item:hover {
  transform: translateX(4px);
}

.rank-num {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-hover);
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
}

.ranking-item.rising .rank-num {
  background: rgba(230, 57, 70, 0.12);
  color: var(--rise-color);
}

.ranking-item.falling .rank-num {
  background: rgba(42, 157, 92, 0.12);
  color: var(--fall-color);
}

.rank-name {
  flex: 1;
  font-size: 13px;
  color: var(--text-primary);
  font-weight: 500;
}

.rank-price {
  font-size: 13px;
  color: var(--text-secondary);
  font-family: 'Fira Code', monospace;
}

.rank-change {
  font-size: 13px;
  font-weight: 600;
  font-family: 'Fira Code', monospace;
}

.rank-change.rise { color: var(--rise-color); }
.rank-change.fall { color: var(--fall-color); }

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

.animate-in {
  opacity: 0;
  animation: fadeInUp 0.5s ease-out forwards;
}

@media (max-width: 1024px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .bottom-grid { grid-template-columns: 1fr; }
}

@media (max-width: 768px) {
  .stats-grid { grid-template-columns: 1fr; }
  .download-buttons { flex-direction: column; }
}
</style>