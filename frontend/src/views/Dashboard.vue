<template>
  <div class="dashboard">
    <header class="header">
      <h1>采购分析助手 - 价格看板</h1>
      <nav>
        <router-link to="/">价格看板</router-link>
        <router-link to="/compare">产品对比</router-link>
      </nav>
    </header>

    <div class="content">
      <div class="stats-cards">
        <el-card class="stat-card">
          <div class="stat-value">{{ stats.total_products }}</div>
          <div class="stat-label">产品总数</div>
        </el-card>
        <el-card class="stat-card">
          <div class="stat-value">{{ stats.total_records }}</div>
          <div class="stat-label">价格记录</div>
        </el-card>
        <el-card class="stat-card">
          <div class="stat-value">{{ stats.avg_price }}</div>
          <div class="stat-label">平均价格 (元/吨)</div>
        </el-card>
      </div>

      <el-card class="chart-card">
        <template #header>
          <div class="card-header">
            <span>价格趋势</span>
            <div class="controls">
              <SourceSelector @update:source="val => { selectedSource = val; loadPriceHistory() }" />
              <el-select v-model="selectedProduct" placeholder="选择产品" size="small" @change="loadPriceHistory">
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

      <el-card class="table-card">
        <template #header>
          <span>最新价格</span>
        </template>
        <el-table :data="latestPrices" style="width: 100%" stripe>
          <el-table-column prop="product_name" label="产品名称" />
          <el-table-column prop="price" label="价格">
            <template #default="{ row }">
              {{ row.price }} 元/吨
            </template>
          </el-table-column>
          <el-table-column prop="trend" label="趋势">
            <template #default="{ row }">
              <span :class="['trend-badge', row.trend]">
                {{ row.trend === '涨' ? '↑' : row.trend === '跌' ? '↓' : '—' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="change_percent" label="涨跌幅">
            <template #default="{ row }">
              <span :class="row.change_percent > 0 ? 'text-rise' : row.change_percent < 0 ? 'text-fall' : ''">
                {{ row.change_percent > 0 ? '+' : '' }}{{ row.change_percent }}%
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="record_date" label="日期" />
        </el-table>
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
let chartInstance = null

async function loadStats() {
  try {
    const res = await priceApi.getStatsSummary()
    stats.value = res.data
  } catch (e) {
    console.error('Failed to load stats', e)
  }
}

async function loadLatestPrices() {
  try {
    const res = await priceApi.getLatestPrices(selectedSource.value)
    latestPrices.value = res.data
  } catch (e) {
    console.error('Failed to load prices', e)
  }
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
    tooltip: {
      trigger: 'axis',
      formatter: '{b}<br/>{a}: {c} 元/吨'
    },
    xAxis: {
      type: 'category',
      data: dates
    },
    yAxis: {
      type: 'value',
      name: '价格'
    },
    series: [{
      name: '价格',
      type: 'line',
      smooth: true,
      data: prices,
      itemStyle: { color: '#409eff' },
      areaStyle: { color: 'rgba(64, 158, 255, 0.1)' }
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
  min-height: 100vh;
}

.header {
  background: #fff;
  padding: 16px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.header h1 {
  font-size: 20px;
  color: #303133;
}

.header nav a {
  margin-left: 20px;
  color: #606266;
  text-decoration: none;
}

.header nav a.router-link-active {
  color: #409eff;
}

.content {
  padding: 20px;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #409eff;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
}

.chart-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.controls {
  display: flex;
  gap: 10px;
}

.chart-container {
  height: 300px;
}

.trend-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: bold;
}

.trend-badge.涨 {
  background: #f56c6c;
  color: #fff;
}

.trend-badge.跌 {
  background: #67c23a;
  color: #fff;
}

.trend-badge.平 {
  background: #909399;
  color: #fff;
}

.text-rise { color: #f56c6c; }
.text-fall { color: #67c23a; }
</style>