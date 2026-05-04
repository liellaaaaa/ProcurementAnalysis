<template>
  <div class="report-view">
    <header class="page-header">
      <div class="header-left">
        <h1 class="page-title">报表中心</h1>
        <p class="page-subtitle">数据分析与报告导出</p>
      </div>
    </header>

    <el-card class="filter-card animate-in">
      <el-form :inline="true" class="filter-form">
        <el-form-item label="报表类型">
          <el-select v-model="reportType" style="width: 130px">
            <el-option label="周报" value="weekly">
              <span class="option-text">◫ 周报</span>
            </el-option>
            <el-option label="月报" value="monthly">
              <span class="option-text">◧ 月报</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="月份" v-if="reportType === 'monthly'">
          <el-date-picker v-model="month" type="month" value-format="YYYY-MM" placeholder="选择月份" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadStats" class="query-btn">
            <span class="btn-icon">◎</span> 查询数据
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="stats-grid">
      <div class="stat-card" v-for="(stat, index) in statCards" :key="stat.label"
           :style="{ animationDelay: `${index * 0.1}s` }">
        <div class="stat-icon" :style="{ background: stat.bgColor }">{{ stat.icon }}</div>
        <div class="stat-content">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
      </div>
    </div>

    <el-card class="download-card animate-in" style="animation-delay: 0.3s">
      <template #header>
        <div class="card-header">
          <div class="header-title">
            <span class="title-icon">◫</span>
            <span>报告导出</span>
          </div>
        </div>
      </template>
      <div class="download-buttons">
        <button class="download-btn pdf" @click="downloadPdf">
          <span class="btn-icon">📄</span>
          <span class="btn-text">下载 PDF 报告</span>
          <span class="btn-desc">适合打印与存档</span>
        </button>
        <button class="download-btn excel" @click="downloadExcel">
          <span class="btn-icon">📊</span>
          <span class="btn-text">下载 Excel 报表</span>
          <span class="btn-desc">便于数据分析处理</span>
        </button>
      </div>
    </el-card>

    <div class="bottom-grid" v-if="forecastData || rankingData.rising.length">
      <el-card class="forecast-card animate-in" style="animation-delay: 0.4s" v-if="forecastData">
        <template #header>
          <div class="card-header">
            <div class="header-title">
              <span class="title-icon">◎</span>
              <span>价格预测 - {{ forecastData.product_name }}</span>
            </div>
          </div>
        </template>
        <div class="forecast-grid">
          <div class="forecast-item">
            <span class="forecast-label">当前价格</span>
            <span class="forecast-value current">¥{{ forecastData.current_price?.toLocaleString() }}</span>
          </div>
          <div class="forecast-item">
            <span class="forecast-label">预测下期</span>
            <span class="forecast-value" :class="forecastData.forecast_next > forecastData.current_price ? 'rise' : 'fall'">
              ¥{{ forecastData.forecast_next?.toLocaleString() }}
            </span>
          </div>
          <div class="forecast-item">
            <span class="forecast-label">7日均价</span>
            <span class="forecast-value">¥{{ forecastData.ma7?.toLocaleString() }}</span>
          </div>
          <div class="forecast-item">
            <span class="forecast-label">30日均价</span>
            <span class="forecast-value">¥{{ forecastData.ma30?.toLocaleString() }}</span>
          </div>
        </div>
        <div class="trend-indicator">
          <span class="trend-label">趋势判断</span>
          <span class="trend-badge" :class="forecastData.trend_direction">
            {{ forecastData.trend_direction }}
          </span>
          <span class="data-points">{{ forecastData.record_count }} 个数据点</span>
        </div>
      </el-card>

      <el-card class="ranking-card animate-in" style="animation-delay: 0.5s" v-if="rankingData.rising.length">
        <template #header>
          <div class="card-header">
            <div class="header-title">
              <span class="title-icon">⬡</span>
              <span>涨跌排行 (近7天)</span>
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
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { reportApi } from '../api/price'

const reportType = ref('weekly')
const month = ref('')
const stats = ref({})
const forecastData = ref(null)
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

    if (products.length > 0) {
      const forecastRes = await reportApi.getForecast(products[0].product_id, 30)
      forecastData.value = forecastRes.data
    }
  } catch (e) {
    ElMessage.error('加载统计数据失败')
  }
}

async function downloadPdf() {
  try {
    const res = await reportApi.downloadPdf(reportType.value)
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
    const res = await reportApi.downloadExcel(reportType.value)
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
  padding: 32px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
}

.page-title {
  font-family: 'Outfit', sans-serif;
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.page-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
}

.filter-card {
  margin-bottom: 24px;
  border-radius: 16px !important;
}

.option-text {
  font-size: 14px;
}

.query-btn {
  padding: 10px 20px !important;
  border-radius: 8px !important;
}

.query-btn .btn-icon {
  margin-right: 6px;
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
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: var(--accent-cyan);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-family: 'Outfit', sans-serif;
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
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
  padding: 4px 0;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: 'Outfit', sans-serif;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.title-icon {
  font-size: 18px;
  color: var(--accent-cyan);
}

.download-buttons {
  display: flex;
  gap: 20px;
  justify-content: center;
  padding: 20px 0;
}

.download-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 28px 48px;
  border: 2px solid var(--border-color);
  border-radius: 16px;
  background: var(--bg-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.download-btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow);
}

.download-btn.pdf:hover {
  border-color: var(--rise-color);
}

.download-btn.excel:hover {
  border-color: var(--fall-color);
}

.download-btn .btn-icon {
  font-size: 32px;
}

.download-btn .btn-text {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.download-btn .btn-desc {
  font-size: 12px;
  color: var(--text-muted);
}

.bottom-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.forecast-card,
.ranking-card {
  border-radius: 16px !important;
}

.forecast-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}

.forecast-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.forecast-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.forecast-value {
  font-family: 'Outfit', sans-serif;
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.forecast-value.rise {
  color: var(--rise-color);
}

.forecast-value.fall {
  color: var(--fall-color);
}

.trend-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border-radius: 10px;
}

.trend-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.trend-badge {
  padding: 4px 12px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
}

.trend-badge.上涨 {
  background: rgba(255, 107, 107, 0.2);
  color: var(--rise-color);
}

.trend-badge.下跌 {
  background: rgba(0, 196, 140, 0.2);
  color: var(--fall-color);
}

.trend-badge.平稳 {
  background: rgba(139, 148, 158, 0.2);
  color: var(--text-secondary);
}

.data-points {
  margin-left: auto;
  font-size: 12px;
  color: var(--text-muted);
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
  background: var(--bg-secondary);
  border-radius: 8px;
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
  background: rgba(255, 107, 107, 0.15);
  color: var(--rise-color);
}

.ranking-item.falling .rank-num {
  background: rgba(0, 196, 140, 0.15);
  color: var(--fall-color);
}

.rank-name {
  flex: 1;
  font-size: 13px;
  color: var(--text-primary);
}

.rank-price {
  font-size: 13px;
  color: var(--text-secondary);
}

.rank-change {
  font-size: 13px;
  font-weight: 600;
}

.rank-change.rise {
  color: var(--rise-color);
}

.rank-change.fall {
  color: var(--fall-color);
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
  opacity: 0;
  animation: fadeInUp 0.5s ease-out forwards;
}
</style>