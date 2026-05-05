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
                <span class="title-icon">◎</span>
                <span>价格走势对比</span>
              </div>
              <div class="controls">
                <el-select v-model="compareDays" placeholder="时间范围" size="default" style="width: 100px" @change="loadCompareData">
                  <el-option label="7天" :value="7" />
                  <el-option label="30天" :value="30" />
                  <el-option label="90天" :value="90" />
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
const compareDays = ref(30)

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
  loadCompareData()
  loadDistributionData()
}

async function loadCompareData() {
  if (!lineChart) return
  try {
    const res = await priceApi.getDashboardHistoryCompare([], compareDays.value)
    if (res.data.series && res.data.series.length > 0) {
      const allDates = [...new Set(res.data.series.flatMap(s => s.dates))].sort()
      const series = res.data.series.map((s, i) => {
        const datePriceMap = {}
        s.dates.forEach((d, idx) => { datePriceMap[d] = s.prices[idx] })
        return {
          name: s.name,
          type: 'line',
          smooth: true,
          data: allDates.map(d => datePriceMap[d] || '-'),
          emphasis: { focus: 'series' }
        }
      })
      lineChart.setOption({
        xAxis: { data: allDates },
        series
      })
    }
  } catch (e) {
    console.error('Failed to load compare data', e)
  }
}

async function loadDistributionData() {
  if (!pieChart) return
  try {
    const res = await priceApi.getDashboardDistribution(30)
    if (res.data.labels && res.data.labels.length > 0) {
      pieChart.setOption({
        series: [{
          data: res.data.labels.map((label, i) => ({
            name: label,
            value: res.data.sizes[i]
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
  // 折线图
  lineChart = echarts.init(lineChartRef.value)
  lineChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: '#21262d', borderColor: '#30363d', textStyle: { color: '#e8eaed' } },
    legend: { bottom: 0, textStyle: { color: '#8b949e' }, selectedMode: false },
    grid: { left: '3%', right: '4%', bottom: '15%', top: '8%', containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, axisLine: { lineStyle: { color: '#30363d' } }, axisLabel: { color: '#8b949e', fontSize: 11 } },
    yAxis: { type: 'value', name: '价格 (元/吨)', nameTextStyle: { color: '#8b949e' }, axisLine: { show: false }, axisLabel: { color: '#8b949e' }, splitLine: { lineStyle: { color: '#30363d', type: 'dashed' } } },
    series: []
  })

  // 饼图
  pieChart = echarts.init(pieChartRef.value)
  pieChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { orient: 'vertical', right: 10, top: 'center', textStyle: { color: '#8b949e' } },
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
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: '#21262d', borderColor: '#30363d', textStyle: { color: '#e8eaed' }, axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '8%', bottom: '3%', top: '3%', containLabel: true },
    xAxis: { type: 'value', axisLine: { show: false }, axisLabel: { color: '#8b949e' }, splitLine: { lineStyle: { color: '#30363d', type: 'dashed' } } },
    yAxis: { type: 'category', data: [], axisLine: { lineStyle: { color: '#30363d' } }, axisLabel: { color: '#8b949e', fontSize: 10 } },
    series: [{
      type: 'bar',
      itemStyle: {
        color: (params) => params.value >= 0 ? '#FF6B6B' : '#4ECDC4',
        borderRadius: [0, 4, 4, 0]
      },
      barWidth: '60%'
    }]
  })

  // 仪表盘
  gaugeChart = echarts.init(gaugeChartRef.value)
  gaugeChart.setOption({
    backgroundColor: 'transparent',
    series: [{
      type: 'gauge',
      startAngle: 180,
      endAngle: 0,
      center: ['50%', '75%'],
      radius: '90%',
      min: 0,
      max: 10,
      splitNumber: 5,
      axisLine: { lineStyle: { width: 8, color: [[1, '#e0e0e0']] } },
      pointer: { itemStyle: { color: '#FF6B6B' }, length: '60%', width: 6 },
      axisTick: { length: 6, lineStyle: { color: '#8b949e' } },
      splitLine: { length: 12, lineStyle: { color: '#8b949e' } },
      axisLabel: { color: '#8b949e', distance: -30, fontSize: 10 },
      detail: { valueAnimation: true, formatter: '{value}%', color: '#e8eaed', fontSize: 20, offsetCenter: [0, '30%'] },
      data: [{ value: 0, name: '平均波动率' }]
    }]
  })
}

async function loadAllDashboardData() {
  await Promise.all([
    loadCompareData(),
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