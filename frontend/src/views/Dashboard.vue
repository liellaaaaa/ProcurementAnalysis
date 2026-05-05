<template>
  <div class="dashboard">
    <header class="page-header">
      <div class="header-left">
        <h1 class="page-title">价格看板</h1>
        <p class="page-subtitle">实时监测市场动态</p>
      </div>
      <div class="header-right">
        <div class="live-indicator">
          <span class="live-dot"></span>
          <span class="live-text">Live Data</span>
        </div>
      </div>
    </header>

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

    <div class="main-grid">
      <el-card class="chart-card animate-in" style="animation-delay: 0.3s">
        <template #header>
          <div class="card-header">
            <div class="header-title">
              <span class="title-icon">◎</span>
              <span>价格趋势</span>
            </div>
            <div class="controls">
              <SourceSelector @update:source="val => { selectedSource = val; loadPriceHistory() }" />
              <el-select v-model="selectedProduct" placeholder="选择产品" size="default" @change="loadPriceHistory">
                <el-option
                  v-for="p in products"
                  :key="p.id"
                  :label="p.product_name"
                  :value="p.id"
                />
              </el-select>
            </div>
          </div>
        </template>
        <div ref="chartRef" class="chart-container"></div>
      </el-card>

      <el-card class="table-card animate-in" style="animation-delay: 0.4s">
        <template #header>
          <div class="card-header">
            <div class="header-title">
              <span class="title-icon">◫</span>
              <span>最新价格</span>
            </div>
            <div class="controls">
              <el-input
                v-model="searchKeyword"
                placeholder="搜索产品"
                size="default"
                style="width: 160px"
                clearable
                @input="debouncedSearch"
              />
              <el-select v-model="selectedSource" placeholder="数据源" size="default" clearable @change="loadLatestPrices" style="width: 120px">
                <el-option label="全部" :value="null" />
                <el-option label="生意社" value="shengyishe" />
              </el-select>
              <span class="record-count">{{ pagination.total }} 条记录</span>
            </div>
          </div>
        </template>
        <el-table :data="latestPrices" style="width: 100%" size="large">
          <el-table-column prop="product_name" label="产品名称" min-width="120" />
          <el-table-column prop="specification" label="规格" min-width="160" show-overflow-tooltip />
          <el-table-column prop="brand" label="品牌" width="100" show-overflow-tooltip />
          <el-table-column prop="region" label="地区" width="90" />
          <el-table-column prop="supplier" label="供应商" width="150" show-overflow-tooltip />
          <el-table-column prop="price" label="价格" width="100">
            <template #default="{ row }">
              <span class="price-value">¥{{ row.price.toLocaleString() }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="trend" label="趋势" width="70">
            <template #default="{ row }">
              <span :class="['trend-badge', row.trend]">
                {{ row.trend === '涨' ? '↑' : row.trend === '跌' ? '↓' : '—' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="change_percent" label="涨跌幅" width="90">
            <template #default="{ row }">
              <span :class="row.change_percent > 0 ? 'text-rise' : row.change_percent < 0 ? 'text-fall' : 'text-flat'">
                {{ row.change_percent > 0 ? '+' : '' }}{{ row.change_percent }}%
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="record_date" label="日期" width="100" />
        </el-table>
        <el-pagination
          v-if="pagination.total > 0"
          background
          layout="prev, pager, next"
          :total="pagination.total"
          :page-size="pagination.pageSize"
          :current-page="pagination.page"
          @current-change="handlePageChange"
          style="margin-top: 16px; justify-content: center"
        />
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { priceApi, productApi } from '../api/price'
import SourceSelector from '../components/SourceSelector.vue'
import * as echarts from 'echarts'

const chartRef = ref(null)
const stats = ref({ total_products: 0, total_records: 0, avg_price: 0 })
const latestPrices = ref([])
const products = ref([])
const selectedProduct = ref(null)
const selectedSource = ref(null)
const searchKeyword = ref('')
const pagination = ref({ page: 1, pageSize: 20, total: 0 })
let chartInstance = null
let searchTimer = null

const statCards = ref([
  { icon: '◈', label: '产品总数', value: 0, bgColor: 'rgba(0, 212, 255, 0.15)' },
  { icon: '◧', label: '价格记录', value: 0, bgColor: 'rgba(255, 107, 107, 0.15)' },
  { icon: '◫', label: '平均价格', value: 0, bgColor: 'rgba(0, 196, 140, 0.15)' }
])

async function loadStats() {
  try {
    const res = await priceApi.getStatsSummary()
    stats.value = res.data
    statCards.value[0].value = res.data.total_products || 0
    statCards.value[1].value = res.data.total_records || 0
    statCards.value[2].value = res.data.avg_price ? `¥${res.data.avg_price.toLocaleString()}` : '-'
  } catch (e) {
    console.error('Failed to load stats', e)
  }
}

async function loadLatestPrices() {
  try {
    const res = await priceApi.getLatestPrices(selectedSource.value, pagination.value.page, pagination.value.pageSize, searchKeyword.value)
    latestPrices.value = res.data.data
    pagination.value.total = res.data.total
  } catch (e) {
    console.error('Failed to load prices', e)
  }
}

function debouncedSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    pagination.value.page = 1
    loadLatestPrices()
  }, 300)
}

function handlePageChange(page) {
  pagination.value.page = page
  loadLatestPrices()
}

async function loadProducts() {
  try {
    const res = await productApi.getProducts({ limit: 100 })
    products.value = res.data
    if (products.value.length > 0 && !selectedProduct.value) {
      selectedProduct.value = products.value[0].id
      loadPriceHistory()
    }
  } catch (e) {
    console.error('Failed to load products', e)
  }
}

async function loadPriceHistory() {
  if (!selectedProduct.value) return

  try {
    const res = await priceApi.getPriceHistory(selectedProduct.value, 30, selectedSource.value)
    updateChart(res.data)
  } catch (e) {
    console.error('Failed to load history', e)
  }
}

function updateChart(data) {
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  const dates = data.map(d => d.record_date)
  const prices = data.map(d => d.price)

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#21262d',
      borderColor: '#30363d',
      textStyle: { color: '#e8eaed' },
      formatter: '{b}<br/><span style="color:#00d4ff">{a}: </span>{c} 元/吨'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      boundaryGap: false,
      axisLine: { lineStyle: { color: '#30363d' } },
      axisLabel: { color: '#8b949e', fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      name: '价格 (元/吨)',
      nameTextStyle: { color: '#8b949e', fontSize: 11 },
      axisLine: { show: false },
      axisLabel: { color: '#8b949e', fontSize: 11 },
      splitLine: { lineStyle: { color: '#30363d', type: 'dashed' } }
    },
    series: [{
      name: '价格',
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      data: prices,
      itemStyle: { color: '#00d4ff' },
      lineStyle: { width: 2 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(0, 212, 255, 0.3)' },
            { offset: 1, color: 'rgba(0, 212, 255, 0.02)' }
          ]
        }
      }
    }]
  }

  chartInstance.setOption(option)
}

onMounted(() => {
  loadStats()
  loadLatestPrices()
  loadProducts()
  window.addEventListener('resize', () => chartInstance?.resize())
})

onUnmounted(() => {
  chartInstance?.dispose()
})
</script>

<style scoped>
.dashboard {
  padding: 32px;
  min-height: 100vh;
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

.live-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--accent-cyan-dim);
  border-radius: 20px;
  border: 1px solid rgba(0, 212, 255, 0.3);
}

.live-dot {
  width: 8px;
  height: 8px;
  background: var(--accent-cyan);
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.2); }
}

.live-text {
  font-size: 12px;
  font-weight: 600;
  color: var(--accent-cyan);
  letter-spacing: 0.5px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  opacity: 0;
  animation: fadeInUp 0.5s ease-out forwards;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: var(--accent-cyan);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-family: 'Outfit', sans-serif;
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.main-grid {
  display: grid;
  gap: 20px;
}

.chart-card {
  border-radius: 16px !important;
}

.table-card {
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

.controls {
  display: flex;
  gap: 12px;
  align-items: center;
}

.record-count {
  font-size: 12px;
  color: var(--text-muted);
  padding: 4px 12px;
  background: var(--bg-hover);
  border-radius: 12px;
}

.chart-container {
  height: 320px;
  margin-top: 16px;
}

.price-value {
  font-family: 'Outfit', sans-serif;
  font-weight: 600;
  color: var(--accent-cyan);
}

.trend-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 24px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
}

.trend-badge.涨 {
  background: rgba(255, 107, 107, 0.2);
  color: var(--rise-color);
}

.trend-badge.跌 {
  background: rgba(0, 196, 140, 0.2);
  color: var(--fall-color);
}

.trend-badge.平 {
  background: rgba(139, 148, 158, 0.2);
  color: var(--text-secondary);
}

.text-rise { color: var(--rise-color); font-weight: 500; }
.text-fall { color: var(--fall-color); font-weight: 500; }
.text-flat { color: var(--text-secondary); }

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