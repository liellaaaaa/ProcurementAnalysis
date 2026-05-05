<template>
  <div class="dashboard">
    <header class="page-header">
      <div class="header-left">
        <h1 class="page-title">数据看板</h1>
        <p class="page-subtitle">采购价格分析仪表台</p>
      </div>
      <div class="header-right">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          size="default"
          style="width: 260px"
          @change="handleDateRangeChange"
        />
      </div>
    </header>

    <!-- 统计卡片 -->
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

    <!-- 图表区域 -->
    <div class="charts-grid">
      <!-- 左侧：折线图 + 饼图 -->
      <div class="charts-left">
        <el-card class="chart-card animate-in" style="animation-delay: 0.2s">
          <template #header>
            <div class="card-header">
              <div class="header-title">
                <span class="title-icon">▦</span>
                <span>产品-地区价格矩阵</span>
              </div>
              <div class="controls">
                <el-select v-model="compareDays" placeholder="时间范围" size="default" style="width: 100px" @change="loadHeatmapData">
                  <el-option label="7天" :value="7" />
                  <el-option label="30天" :value="30" />
                </el-select>
              </div>
            </div>
          </template>
          <div ref="lineChartRef" class="chart-container"></div>
        </el-card>

        <el-card class="chart-card animate-in" style="animation-delay: 0.3s">
          <template #header>
            <div class="card-header">
              <div class="header-title">
                <span class="title-icon">◉</span>
                <span>产品价格占比</span>
              </div>
            </div>
          </template>
          <div ref="pieChartRef" class="chart-container-small"></div>
        </el-card>
      </div>

      <!-- 右侧：柱状图 + 仪表盘 -->
      <div class="charts-right">
        <el-card class="chart-card animate-in" style="animation-delay: 0.4s">
          <template #header>
            <div class="card-header">
              <div class="header-title">
                <span class="title-icon">▤</span>
                <span>涨跌排行 TOP10</span>
              </div>
            </div>
          </template>
          <div ref="barChartRef" class="chart-container-small"></div>
        </el-card>

        <el-card class="chart-card animate-in" style="animation-delay: 0.5s">
          <template #header>
            <div class="card-header">
              <div class="header-title">
                <span class="title-icon">◔</span>
                <span>价格波动监控</span>
              </div>
            </div>
          </template>
          <div ref="gaugeChartRef" class="chart-container-small"></div>
        </el-card>
      </div>
    </div>

    <!-- 最新价格表格 -->
    <el-card class="table-card animate-in" style="animation-delay: 0.6s">
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
      <el-table :data="latestPrices" style="width: 100%" size="large" row-key="product_id" :expand-row-keys="expandedRows" @expand-change="handleExpandChange">
        <el-table-column type="expand" width="50">
          <template #default="{ row }">
            <div class="expand-content">
              <p class="expand-title">各供应商/地区价格明细</p>
              <el-table :data="row.details" size="small" class="detail-table">
                <el-table-column prop="supplier" label="供应商" min-width="140" show-overflow-tooltip />
                <el-table-column prop="region" label="地区" width="100" />
                <el-table-column prop="brand" label="品牌" width="120" show-overflow-tooltip />
                <el-table-column prop="specification" label="规格" min-width="160" show-overflow-tooltip />
                <el-table-column prop="price" label="价格" width="100">
                  <template #default="{ row: detail }">
                    <span class="price-value">¥{{ detail.price.toLocaleString() }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="trend" label="趋势" width="70">
                  <template #default="{ row: detail }">
                    <span :class="['trend-badge', detail.trend]">
                      {{ detail.trend === '涨' ? '↑' : detail.trend === '跌' ? '↓' : '—' }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="change_percent" label="涨跌幅" width="90">
                  <template #default="{ row: detail }">
                    <span :class="detail.change_percent > 0 ? 'text-rise' : detail.change_percent < 0 ? 'text-fall' : 'text-flat'">
                      {{ detail.change_percent > 0 ? '+' : '' }}{{ detail.change_percent }}%
                    </span>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="product_name" label="产品名称" min-width="120" />
        <el-table-column label="价格区间" min-width="140">
          <template #default="{ row }">
            <span class="price-range">
              <span class="price-value">¥{{ row.min_price.toLocaleString() }}</span>
              <span class="price-separator">~</span>
              <span class="price-value">¥{{ row.max_price.toLocaleString() }}</span>
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
        <el-table-column prop="trend" label="趋势" width="70">
          <template #default="{ row }">
            <span :class="['trend-badge', row.trend]">
              {{ row.trend === '涨' ? '↑' : row.trend === '跌' ? '↓' : '—' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="record_date" label="日期" width="100" />
        <el-table-column label="供应商数" width="90">
          <template #default="{ row }">
            <span class="detail-count">{{ row.details ? row.details.length : 0 }}家</span>
          </template>
        </el-table-column>
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
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { priceApi, productApi } from '../api/price'
import * as echarts from 'echarts'

const lineChartRef = ref(null)
const pieChartRef = ref(null)
const barChartRef = ref(null)
const gaugeChartRef = ref(null)

const stats = ref({ total_products: 0, total_records: 0, avg_price: 0 })
const latestPrices = ref([])
const selectedSource = ref(null)
const searchKeyword = ref('')
const dateRange = ref([])
const compareDays = ref(7)
const expandedRows = ref([])

const pagination = ref({ page: 1, pageSize: 20, total: 0 })

let lineChart = null
let pieChart = null
let barChart = null
let gaugeChart = null
let searchTimer = null

const statCards = ref([
  { icon: '◈', label: '产品总数', value: 0, bgColor: 'rgba(0, 212, 255, 0.15)' },
  { icon: '◧', label: '价格记录', value: 0, bgColor: 'rgba(255, 107, 107, 0.15)' },
  { icon: '◫', label: '平均价格', value: 0, bgColor: 'rgba(0, 196, 140, 0.15)' },
  { icon: '◇', label: '今日更新', value: 0, bgColor: 'rgba(255, 159, 67, 0.15)' }
])

async function loadStats() {
  try {
    const [summaryRes, volatilityRes] = await Promise.all([
      priceApi.getStatsSummary(),
      priceApi.getDashboardVolatility(1)
    ])
    stats.value = summaryRes.data
    statCards.value[0].value = summaryRes.data.total_products || 0
    statCards.value[1].value = summaryRes.data.total_records || 0
    statCards.value[2].value = summaryRes.data.avg_price ? `¥${summaryRes.data.avg_price.toLocaleString()}` : '-'
    statCards.value[3].value = volatilityRes.data.today_updated || 0
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

function handleDateRangeChange() {
  loadHeatmapData()
  loadDistributionData()
}

function handleExpandChange(row) {
  const id = row.product_id
  if (expandedRows.value.includes(id)) {
    expandedRows.value = []
  } else {
    expandedRows.value = [id]
  }
}

async function loadHeatmapData() {
  if (!lineChart) return
  try {
    const res = await priceApi.getDashboardHeatmap(compareDays.value)
    const { products, regions, data } = res.data

    if (!products || products.length === 0 || !regions || regions.length === 0) {
      lineChart.setOption({ series: [{ data: [] }] })
      return
    }

    // 计算价格范围
    const prices = data.map(d => d.price)
    const minPrice = Math.min(...prices)
    const maxPrice = Math.max(...prices)

    // 构建矩阵热力图数据：[地区索引, 产品索引, 价格]
    const heatmapData = data.map(d => [
      regions.indexOf(d.region),
      products.findIndex(p => p.id === d.product_id),
      d.price
    ])

    lineChart.setOption({
      tooltip: {
        trigger: 'item',
        backgroundColor: '#fff',
        borderColor: '#ddd',
        borderWidth: 1,
        textStyle: { color: '#333', fontSize: 12 },
        formatter: (params) => {
          const region = regions[params.value[0]]
          const product = products[params.value[1]].name
          const price = params.value[2]
          return `<strong>${product}</strong><br/>地区: ${region}<br/>价格: <strong style="color:#c62828">¥${price.toLocaleString()}</strong>`
        }
      },
      grid: {
        left: 10,
        right: 80,
        bottom: 15,
        top: 10
      },
      xAxis: {
        type: 'category',
        data: regions,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#666', fontSize: 10, rotate: 30 },
        splitArea: { show: false }
      },
      yAxis: {
        type: 'category',
        data: products.map(p => p.name),
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#666', fontSize: 10, width: 100, overflow: 'truncate' },
        splitArea: { show: false }
      },
      visualMap: {
        type: 'continuous',
        min: minPrice,
        max: maxPrice,
        calculable: true,
        orient: 'vertical',
        right: 0,
        top: 'center',
        textStyle: { color: '#666', fontSize: 10 },
        inRange: {
          color: ['#ffebee', '#ffcdd2', '#ef9a9a', '#e57373', '#c62828', '#7b0000']
        },
        formatter: (val) => `¥${val.toFixed(0)}`
      },
      series: [{
        type: 'heatmap',
        data: heatmapData,
        emphasis: {
          itemStyle: {
            borderColor: '#333',
            borderWidth: 2,
            shadowBlur: 6,
            shadowColor: 'rgba(0,0,0,0.25)'
          }
        },
        itemStyle: {
          borderColor: '#fff',
          borderWidth: 1,
          borderRadius: 2
        }
      }]
    }, true)
  } catch (e) {
    console.error('Failed to load heatmap data', e)
  }
}

async function loadDistributionData() {
  if (!pieChart) return
  try {
    const res = await priceApi.getDashboardDistribution(30)
    if (res.data.labels && res.data.labels.length > 0) {
      const pieColors = ['#0077cc', '#00c48c', '#ff6b6b', '#ffd93d', '#9b59b6', '#3498db', '#e67e22', '#1abc9c', '#e91e63', '#6739b6']
      pieChart.setOption({
        series: [{
          data: res.data.labels.map((label, i) => ({
            name: label,
            value: res.data.sizes[i],
            itemStyle: { color: pieColors[i % pieColors.length] }
          }))
        }]
      })
    }
  } catch (e) {
    console.error('Failed to load distribution data', e)
  }
}

async function loadRankingData() {
  if (!barChart) return
  try {
    const res = await priceApi.getDashboardRanking(10, 7)
    const rising = res.data.rising || []
    if (rising.length > 0) {
      const categories = rising.map(r => r.product_name.substring(0, 8))
      const values = rising.map(r => r.change_percent)
      barChart.setOption({
        yAxis: { data: categories },
        series: [{ data: values }]
      })
    }
  } catch (e) {
    console.error('Failed to load ranking data', e)
  }
}

async function loadVolatilityData() {
  if (!gaugeChart) return
  try {
    const res = await priceApi.getDashboardVolatility(7)
    const value = res.data.avg_volatility || 0
    const maxVal = Math.max(res.data.max_volatility || 10, 10)
    gaugeChart.setOption({
      series: [{
        type: 'gauge',
        startAngle: 180,
        endAngle: 0,
        min: 0,
        max: maxVal,
        splitNumber: 5,
        axisLine: {
          lineStyle: {
            width: 8,
            color: [[0.3, '#4ECDC4'], [0.7, '#45B7D1'], [1, '#FF6B6B']]
          }
        },
        pointer: { itemStyle: { color: '#FF6B6B' }, length: '60%', width: 6 },
        axisTick: { length: 6, lineStyle: { color: '#8b949e' } },
        splitLine: { length: 12, lineStyle: { color: '#8b949e' } },
        axisLabel: { color: '#8b949e', distance: -30, fontSize: 10 },
        detail: { valueAnimation: true, formatter: '{value}%', color: '#e8eaed', fontSize: 20, offsetCenter: [0, '30%'] },
        data: [{ value: value, name: '平均波动率' }]
      }]
    })
  } catch (e) {
    console.error('Failed to load volatility data', e)
  }
}

function initCharts() {
  // 热力图：产品-地区矩阵
  lineChart = echarts.init(lineChartRef.value)
  lineChart.setOption({
    backgroundColor: '#ffffff',
    tooltip: { trigger: 'item', backgroundColor: '#fff', borderColor: '#ddd', textStyle: { color: '#333' } },
    grid: { left: 10, right: 80, bottom: 15, top: 10 },
    xAxis: { type: 'category', data: [], axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#666', fontSize: 10, rotate: 30 }, splitArea: { show: false } },
    yAxis: { type: 'category', data: [], axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#666', fontSize: 10, width: 100, overflow: 'truncate' }, splitArea: { show: false } },
    visualMap: { type: 'continuous', min: 0, max: 10000, calculable: true, orient: 'vertical', right: 0, top: 'center', textStyle: { color: '#666', fontSize: 10 }, inRange: { color: ['#ffebee', '#ffcdd2', '#ef9a9a', '#e57373', '#c62828', '#7b0000'] }, formatter: (val) => `¥${val.toFixed(0)}` },
    series: [{ type: 'heatmap', data: [], emphasis: { itemStyle: { borderColor: '#333', borderWidth: 2, shadowBlur: 6, shadowColor: 'rgba(0,0,0,0.25)' } }, itemStyle: { borderColor: '#fff', borderWidth: 1, borderRadius: 2 } }]
  })

  // 饼图
  pieChart = echarts.init(pieChartRef.value)
  pieChart.setOption({
    backgroundColor: '#ffffff',
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)', backgroundColor: '#ffffff', borderColor: '#e4e7ed', textStyle: { color: '#1a1a2e' } },
    legend: { orient: 'vertical', right: 10, top: 'center', textStyle: { color: '#5a6178' } },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['35%', '50%'],
      label: { show: false },
      emphasis: { label: { show: false } }
    }]
  })

  // 柱状图
  barChart = echarts.init(barChartRef.value)
  barChart.setOption({
    backgroundColor: '#ffffff',
    tooltip: { trigger: 'axis', backgroundColor: '#ffffff', borderColor: '#e4e7ed', textStyle: { color: '#1a1a2e' }, axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '8%', bottom: '3%', top: '3%', containLabel: true },
    xAxis: { type: 'value', axisLine: { show: false }, axisLabel: { color: '#5a6178' }, splitLine: { lineStyle: { color: '#e4e7ed', type: 'dashed' } } },
    yAxis: { type: 'category', data: [], axisLine: { lineStyle: { color: '#e4e7ed' } }, axisLabel: { color: '#5a6178', fontSize: 10 } },
    series: [{
      type: 'bar',
      itemStyle: {
        color: (params) => params.value >= 0 ? '#e53935' : '#2e7d32',
        borderRadius: [0, 4, 4, 0]
      },
      barWidth: '60%'
    }]
  })

  // 仪表盘
  gaugeChart = echarts.init(gaugeChartRef.value)
  gaugeChart.setOption({
    backgroundColor: '#ffffff',
    series: [{
      type: 'gauge',
      startAngle: 180,
      endAngle: 0,
      center: ['50%', '75%'],
      radius: '90%',
      min: 0,
      max: 10,
      splitNumber: 5,
      axisLine: { lineStyle: { width: 8, color: [[1, '#e4e7ed']] } },
      pointer: { itemStyle: { color: '#e53935' }, length: '60%', width: 6 },
      axisTick: { length: 6, lineStyle: { color: '#5a6178' } },
      splitLine: { length: 12, lineStyle: { color: '#5a6178' } },
      axisLabel: { color: '#5a6178', distance: -30, fontSize: 10 },
      detail: { valueAnimation: true, formatter: '{value}%', color: '#1a1a2e', fontSize: 20, offsetCenter: [0, '30%'] },
      data: [{ value: 0, name: '平均波动率' }]
    }]
  })
}

async function loadAllDashboardData() {
  await Promise.all([
    loadHeatmapData(),
    loadDistributionData(),
    loadRankingData(),
    loadVolatilityData()
  ])
}

onMounted(async () => {
  await nextTick()
  initCharts()
  loadStats()
  loadLatestPrices()
  loadAllDashboardData()
  window.addEventListener('resize', () => {
    lineChart?.resize()
    pieChart?.resize()
    barChart?.resize()
    gaugeChart?.resize()
  })
})

onUnmounted(() => {
  lineChart?.dispose()
  pieChart?.dispose()
  barChart?.dispose()
  gaugeChart?.dispose()
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

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 24px;
}

.charts-left, .charts-right {
  display: grid;
  gap: 20px;
}

.chart-card {
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

.chart-container-small {
  height: 220px;
  margin-top: 16px;
}

.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 20px 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  opacity: 0;
  animation: fadeInUp 0.5s ease-out forwards;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow);
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
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.table-card {
  border-radius: 16px !important;
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

.trend-badge.涨 { background: rgba(255, 107, 107, 0.2); color: var(--rise-color); }
.trend-badge.跌 { background: rgba(0, 196, 140, 0.2); color: var(--fall-color); }
.trend-badge.平 { background: rgba(139, 148, 158, 0.2); color: var(--text-secondary); }

.price-range {
  display: flex;
  align-items: center;
  gap: 4px;
  font-family: 'Outfit', sans-serif;
}

.price-separator {
  color: var(--text-muted);
  margin: 0 2px;
}

.detail-count {
  font-size: 12px;
  color: var(--text-muted);
  padding: 2px 8px;
  background: var(--bg-hover);
  border-radius: 8px;
}

.expand-content {
  padding: 8px 16px;
  background: var(--bg-elevated);
  border-radius: 8px;
  margin: 8px 0;
}

.expand-title {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 12px;
  font-weight: 500;
}

.detail-table {
  background: transparent !important;
}

.text-rise { color: var(--rise-color); font-weight: 500; }
.text-fall { color: var(--fall-color); font-weight: 500; }
.text-flat { color: var(--text-secondary); }

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

.animate-in {
  opacity: 0;
  animation: fadeInUp 0.5s ease-out forwards;
}

@media (max-width: 1200px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .charts-grid { grid-template-columns: 1fr; }
}

@media (max-width: 768px) {
  .stats-grid { grid-template-columns: 1fr; }
}
</style>