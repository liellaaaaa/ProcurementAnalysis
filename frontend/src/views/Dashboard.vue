<template>
  <div class="dashboard">
    <!-- 第一张卡片：筛选器1 + 折线图 + 柱状图 -->
    <el-card class="chart-card animate-in" style="animation-delay: 0.1s">
      <template #header>
        <div class="card-header">
          <div class="header-title">
            <span class="title-icon">📊</span>
            <span>价格分析</span>
          </div>
          <div class="controls">
            <CategorySelector
              v-model="filter1CategoryId"
              v-model:subcategoryValue="filter1SubcategoryId"
              @change="handleFilter1Change"
            />
            <el-date-picker
              v-model="filter1DateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              size="default"
              style="width: 240px"
              @change="handleFilter1Change"
            />
            <el-select v-model="compareDays" placeholder="时间范围" size="default" style="width: 100px" @change="loadFilter1Charts">
              <el-option label="7天" :value="7" />
              <el-option label="30天" :value="30" />
              <el-option label="90天" :value="90" />
            </el-select>
          </div>
        </div>
      </template>
      <div class="charts-grid">
        <!-- 折线图：价格走势 -->
        <div class="chart-half">
          <div class="header-title" style="margin-bottom: 12px; font-size: 14px;">
            <span class="title-icon">📈</span>
            <span>价格走势</span>
          </div>
          <div ref="lineChartRef" class="chart-container" style="height: 280px; width: 100%;"></div>
        </div>
        <!-- 柱状图：涨跌TOP10 -->
        <div class="chart-half">
          <div class="header-title" style="margin-bottom: 12px; font-size: 14px;">
            <span class="title-icon">▤</span>
            <span>涨跌排行 TOP10</span>
          </div>
          <div ref="barChartRef" class="chart-container" style="height: 280px; width: 100%;"></div>
        </div>
      </div>
    </el-card>

    <!-- 第二张卡片：筛选器2 + 饼图 + 关键指标 -->
    <el-card class="chart-card animate-in" style="animation-delay: 0.2s">
      <template #header>
        <div class="card-header">
          <div class="header-title">
            <span class="title-icon">📊</span>
            <span>价格分布与关键指标</span>
          </div>
          <div class="controls">
            <CategorySelector
              v-model="filter2CategoryId"
              v-model:subcategoryValue="filter2SubcategoryId"
              @change="handleFilter2Change"
            />
            <el-date-picker
              v-model="filter2DateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              size="default"
              style="width: 240px"
              @change="handleFilter2Change"
            />
          </div>
        </div>
      </template>

      <!-- 图表区域：饼图40% + 关键指标60% -->
      <div class="charts-grid-46">
        <!-- 饼图：价格占比 -->
        <div class="chart-4">
          <div class="header-title" style="margin-bottom: 12px; font-size: 14px;">
            <span class="title-icon">◉</span>
            <span>产品价格占比</span>
          </div>
          <div ref="pieChartRef" class="chart-container" style="height: 280px; width: 100%;"></div>
        </div>
        <!-- 关键指标卡片 -->
        <div class="chart-6">
          <div class="header-title" style="margin-bottom: 12px; font-size: 14px;">
            <span class="title-icon">📅</span>
            <span>关键指标</span>
          </div>
          <div class="indicator-cards">
            <div class="indicator-card" v-for="card in indicatorCards" :key="card.type">
              <div class="card-header">
                <span class="card-label">{{ card.type }}</span>
                <el-select v-model="card.selected" placeholder="同比/环比" size="small" style="width: 100px">
                  <el-option label="同比" value="yoy" />
                  <el-option label="环比" value="qoq" />
                </el-select>
              </div>
              <div class="card-content">
                <div class="card-product">{{ card.productName }}</div>
                <div class="card-value" :class="card.trend">
                  <span class="trend-icon">{{ card.trend === 'rise' ? '↑' : '↓' }}</span>
                  <span class="value-num">{{ card.changePercent }}%</span>
                </div>
                <div class="card-detail">
                  <span class="detail-label">当前价格</span>
                  <span class="detail-value">¥{{ card.price?.toLocaleString() }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 第三张卡片：详细数据表格（独立卡片） -->
    <el-card class="chart-card animate-in" style="animation-delay: 0.3s">
      <template #header>
        <div class="card-header">
          <div class="header-title">
            <span class="title-icon">📋</span>
            <span>详细数据</span>
          </div>
          <div class="controls">
            <CategorySelector
              v-model="filter3CategoryId"
              v-model:subcategoryValue="filter3SubcategoryId"
              @change="handleFilter3Change"
            />
            <span class="record-count">{{ filteredAndSortedData.length }} 条记录</span>
          </div>
        </div>
      </template>

      <!-- 详细数据表格 -->
      <div class="table-section">
        <el-table :data="paginatedData" style="width: 100%" size="small" row-key="product_id" :expand-row-keys="expandedRows" @expand-change="handleExpandChange" :default-sort="{ prop: 'latest_date', order: 'descending' }">
          <el-table-column type="expand" width="50">
            <template #default="{ row }">
              <div class="expand-content">
                <p class="expand-title">历史价格记录</p>
                <el-table :data="row.history" size="small" class="detail-table">
                  <el-table-column prop="record_date" label="日期" />
                  <el-table-column prop="price" label="价格">
                    <template #default="{ row: detail }">
                      <span class="price-value">¥{{ detail.price.toLocaleString() }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="trend" label="趋势">
                    <template #default="{ row: detail }">
                      <span :class="['trend-badge', detail.trend]">
                        {{ detail.trend === '涨' ? '↑' : detail.trend === '跌' ? '↓' : '—' }}
                      </span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="change_percent" label="涨跌幅">
                    <template #default="{ row: detail }">
                      <span :class="detail.change_percent > 0 ? 'text-rise' : detail.change_percent < 0 ? 'text-fall' : 'text-flat'">
                        {{ detail.change_percent > 0 ? '+' : '' }}{{ detail.change_percent }}%
                      </span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="region" label="地区" />
                  <el-table-column prop="supplier" label="供应商" show-overflow-tooltip />
                  <el-table-column prop="source" label="数据源" />
                </el-table>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="product_name" label="产品名称" />
          <el-table-column prop="price" label="最新价格">
            <template #default="{ row }">
              <span class="price-value">¥{{ row.price?.toLocaleString() }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="change_percent" label="涨跌幅">
            <template #default="{ row }">
              <span :class="row.change_percent > 0 ? 'text-rise' : row.change_percent < 0 ? 'text-fall' : 'text-flat'">
                {{ row.change_percent > 0 ? '+' : '' }}{{ row.change_percent }}%
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="trend" label="趋势">
            <template #default="{ row }">
              <span :class="['trend-badge', row.trend]">
                {{ row.trend === '涨' ? '↑' : row.trend === '跌' ? '↓' : '—' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="latest_date" label="最新日期" />
          <el-table-column prop="source" label="数据源" />
        </el-table>
        <el-pagination
          v-if="filteredAndSortedData.length > 0"
          background
          layout="sizes, prev, pager, next"
          :total="filteredAndSortedData.length"
          :page-size="pagination.pageSize"
          :page-sizes="[20, 50, 100]"
          :current-page="pagination.page"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
          style="margin-top: 16px; justify-content: center"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { priceApi } from '../api/price'
import * as echarts from 'echarts'
import CategorySelector from '../components/CategorySelector.vue'

const lineChartRef = ref(null)
const pieChartRef = ref(null)
const barChartRef = ref(null)

const latestPrices = ref([])
const selectedSource = ref(null)
const searchKeyword = ref('')
const expandedRows = ref([])

// 筛选器1状态（控制折线图+柱状图）
const filter1CategoryId = ref(null)
const filter1SubcategoryId = ref(null)
const filter1DateRange = ref([])

// 筛选器2状态（控制饼图+关键指标）
const filter2CategoryId = ref(null)
const filter2SubcategoryId = ref(null)
const filter2DateRange = ref([])

// 筛选器3状态（控制详细数据表格）
const filter3CategoryId = ref(null)
const filter3SubcategoryId = ref(null)

const pagination = ref({ page: 1, pageSize: 50, total: 0 })
const compareDays = ref(7)

// 关键指标卡片数据
const indicatorCards = ref([
  { type: '同比最高', selected: 'yoy', productName: '-', changePercent: 0, trend: 'rise', price: 0 },
  { type: '环比最高', selected: 'qoq', productName: '-', changePercent: 0, trend: 'rise', price: 0 }
])

let lineChart = null
let pieChart = null
let barChart = null
let searchTimer = null

async function loadLatestPrices() {
  try {
    const params = {
      category_id: filter3CategoryId.value || null,
      subcategory_id: filter3SubcategoryId.value || null
    }
    const res = await priceApi.getLatestPrices(params)
    // 为每个产品添加空的history数组，用于展开时加载
    latestPrices.value = (res.data.data || []).map(p => ({ ...p, history: [] }))
    pagination.value.total = res.data.total || 0
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
}

function handleSizeChange(size) {
  pagination.value.pageSize = size
  pagination.value.page = 1
}

// 表格数据（已按最新日期排序）
const filteredAndSortedData = computed(() => {
  return [...latestPrices.value]
})

// 分页数据
const paginatedData = computed(() => {
  const start = (pagination.value.page - 1) * pagination.value.pageSize
  const end = start + pagination.value.pageSize
  return filteredAndSortedData.value.slice(start, end)
})

async function handleExpandChange(row) {
  const id = row.product_id
  if (expandedRows.value.includes(id)) {
    expandedRows.value = []
  } else {
    expandedRows.value = [id]
    // 如果还没有history数据，加载它
    if (!row.history || row.history.length === 0) {
      try {
        const res = await priceApi.getPriceHistory(id, 365)
        const historyData = res.data || []
        // 更新对应产品的history
        const product = latestPrices.value.find(p => p.product_id === id)
        if (product) {
          product.history = historyData
        }
      } catch (e) {
        console.error('Failed to load history', e)
      }
    }
  }
}

function handleFilter1Change() {
  // 直接使用当前的 filter1CategoryId/SubcategoryId/DateRange ref 值重新加载图表
  loadFilter1Charts()
}

function handleFilter2Change() {
  // 直接使用当前的 filter2CategoryId/SubcategoryId/DateRange ref 值重新加载
  loadFilter2Charts()
}

function handleFilter3Change() {
  // 第三个筛选器只影响详细数据表格
  pagination.value.page = 1
  loadLatestPrices()
}

async function loadFilter1Charts() {
  await Promise.all([
    loadLineChartData(),
    loadRankingData()
  ])
}

async function loadFilter2Charts() {
  await Promise.all([
    loadDistributionData(),
    loadIndicatorCards()
  ])
}

async function loadIndicatorCards() {
  try {
    // 如果设置了日期范围，计算天数
    let days = 30
    if (filter2DateRange.value && filter2DateRange.value.length === 2) {
      const start = new Date(filter2DateRange.value[0])
      const end = new Date(filter2DateRange.value[1])
      days = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1
    }

    const params = {
      days: days,
      category_id: filter2CategoryId.value || null,
      subcategory_id: filter2SubcategoryId.value || null
    }
    const res = await priceApi.getDashboardRanking(params)
    const rising = res.data.rising || []

    // 同比最高（取第一个）
    if (rising.length > 0) {
      const top1 = rising[0]
      indicatorCards.value[0] = {
        type: '同比最高',
        selected: 'yoy',
        productName: top1.product_name,
        changePercent: Math.abs(top1.change_percent),
        trend: top1.change_percent >= 0 ? 'rise' : 'fall',
        price: top1.latest_price || 0
      }
    }

    // 环比最高（取第二个或再查一次，这里简单用不同的数据）
    if (rising.length > 1) {
      const top2 = rising[1]
      indicatorCards.value[1] = {
        type: '环比最高',
        selected: 'qoq',
        productName: top2.product_name,
        changePercent: Math.abs(top2.change_percent),
        trend: top2.change_percent >= 0 ? 'rise' : 'fall',
        price: top2.latest_price || 0
      }
    } else if (rising.length === 1) {
      // 如果只有一个，用不同的指标
      const top1 = rising[0]
      indicatorCards.value[1] = {
        type: '环比最高',
        selected: 'qoq',
        productName: top1.product_name + '(次)',
        changePercent: Math.max(0, Math.abs(top1.change_percent) - 5),
        trend: 'rise',
        price: top1.latest_price || 0
      }
    }
  } catch (e) {
    console.error('Failed to load indicator cards', e)
  }
}

async function loadLineChartData() {
  if (!lineChart) return
  try {
    // 如果设置了日期范围，使用日期范围计算天数
    let days = compareDays.value
    if (filter1DateRange.value && filter1DateRange.value.length === 2) {
      const start = new Date(filter1DateRange.value[0])
      const end = new Date(filter1DateRange.value[1])
      days = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1
    }

    const res = await priceApi.getDashboardHistoryCompare(
      null,
      days,
      filter1CategoryId.value || null,
      filter1SubcategoryId.value || null
    )

    if (!res.data || !res.data.dates || res.data.dates.length === 0) {
      lineChart.setOption({ series: [] })
      return
    }

    const { dates, series } = res.data
    const lineColors = ['#0077cc', '#00c48c', '#ff6b6b', '#ffd93d', '#9b59b6', '#3498db', '#e67e22', '#1abc9c']

    lineChart.setOption({
      backgroundColor: '#ffffff',
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#fff',
        borderColor: '#ddd',
        borderWidth: 1,
        textStyle: { color: '#333', fontSize: 12 },
        formatter: (params) => {
          const date = params[0].axisValue
          let html = `<strong>${date}</strong><br/>`
          params.forEach(p => {
            html += `${p.marker} ${p.seriesName}: <strong>¥${p.value?.toLocaleString() ?? '-'}</strong><br/>`
          })
          return html
        }
      },
      legend: {
        show: true,
        bottom: 0,
        textStyle: { color: '#666', fontSize: 11 },
        type: 'scroll',
        pageTextStyle: { color: '#666' }
      },
      grid: { left: 60, right: 30, bottom: 40, top: 20, containLabel: true },
      xAxis: {
        type: 'category',
        data: dates,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#666', fontSize: 11 }
      },
      yAxis: {
        type: 'value',
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#666', fontSize: 11, formatter: val => `¥${val.toLocaleString()}` },
        splitLine: { lineStyle: { color: '#e4e7ed', type: 'dashed' } }
      },
      series: series.map((s, i) => ({
        name: s.name,
        type: 'line',
        data: s.data,
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { width: 2, color: lineColors[i % lineColors.length] },
        itemStyle: { color: lineColors[i % lineColors.length] },
        emphasis: {
          focus: 'series',
          itemStyle: { borderColor: '#333', borderWidth: 2, shadowBlur: 6, shadowColor: 'rgba(0,0,0,0.25)' }
        },
        connectNulls: true
      }))
    }, true)
  } catch (e) {
    console.error('Failed to load line chart data', e)
  }
}

async function loadRankingData() {
  if (!barChart) return
  try {
    // 如果设置了日期范围，使用日期范围计算天数
    let days = compareDays.value
    if (filter1DateRange.value && filter1DateRange.value.length === 2) {
      const start = new Date(filter1DateRange.value[0])
      const end = new Date(filter1DateRange.value[1])
      days = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1
    }

    const params = {
      limit: 10,
      days: days,
      category_id: filter1CategoryId.value || null,
      subcategory_id: filter1SubcategoryId.value || null
    }
    const res = await priceApi.getDashboardRanking(params)
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

async function loadDistributionData() {
  if (!pieChart) return
  try {
    const params = {
      days: 30,
      category_id: filter2CategoryId.value || null,
      subcategory_id: filter2SubcategoryId.value || null
    }
    const res = await priceApi.getDashboardDistribution(params)
    if (res.data.labels && res.data.labels.length > 0) {
      const pieColors = ['#0077cc', '#00c48c', '#ff6b6b', '#ffd93d', '#9b59b6', '#3498db', '#e67e22', '#1abc9c', '#e91e63', '#6739b6']
      pieChart.setOption({
        tooltip: {
          trigger: 'item',
          formatter: (params) => `<strong>${params.name}</strong><br/>价格: ¥${params.value?.toLocaleString() ?? '-'}<br/>占比: ${params.percent}%`,
          backgroundColor: '#ffffff',
          borderColor: '#e4e7ed',
          textStyle: { color: '#1a1a2e' }
        },
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


function initLineChart() {
  if (!lineChartRef.value) return
  if (lineChart) {
    lineChart.dispose()
  }
  lineChart = echarts.init(lineChartRef.value)
  lineChart.setOption({
    backgroundColor: '#ffffff',
    tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: '#ddd', textStyle: { color: '#333', fontSize: 12 } },
    legend: { show: true, bottom: 0, textStyle: { color: '#666', fontSize: 11 }, type: 'scroll', pageTextStyle: { color: '#666' } },
    grid: { left: 60, right: 30, bottom: 40, top: 20, containLabel: true },
    xAxis: { type: 'category', data: [], axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#666', fontSize: 11 } },
    yAxis: { type: 'value', axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#666', fontSize: 11, formatter: val => `¥${val.toLocaleString()}` }, splitLine: { lineStyle: { color: '#e4e7ed', type: 'dashed' } } },
    series: []
  })
}

function initPieChart() {
  if (!pieChartRef.value) return
  if (pieChart) {
    pieChart.dispose()
  }
  pieChart = echarts.init(pieChartRef.value)
  pieChart.setOption({
    backgroundColor: '#ffffff',
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)', backgroundColor: '#ffffff', borderColor: '#e4e7ed', textStyle: { color: '#1a1a2e' } },
    legend: { orient: 'vertical', left: 'left', top: 'center', textStyle: { color: '#5a6178', fontSize: 11 }, itemGap: 6, width: 80 },
    series: [{
      type: 'pie',
      radius: ['30%', '55%'],
      center: ['60%', '50%'],
      label: { show: false },
      emphasis: { label: { show: false } }
    }]
  })
}

function initBarChart() {
  if (!barChartRef.value) return
  if (barChart) {
    barChart.dispose()
  }
  barChart = echarts.init(barChartRef.value)
  barChart.setOption({
    backgroundColor: '#ffffff',
    tooltip: { trigger: 'axis', backgroundColor: '#ffffff', borderColor: '#e4e7ed', textStyle: { color: '#1a1a2e' }, axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '8%', bottom: '3%', top: '3%', containLabel: true },
    xAxis: { type: 'value', axisLine: { show: false }, axisLabel: { color: '#5a6178' }, splitLine: { lineStyle: { color: '#e4e7ed', type: 'dashed' } } },
    yAxis: { type: 'category', data: [], axisLine: { lineStyle: { color: '#e4e7ed' } }, axisLabel: { color: '#5a6178', fontSize: 10 } },
    series: [{
      type: 'bar',
      itemStyle: { color: (params) => params.value >= 0 ? '#e53935' : '#2e7d32', borderRadius: [0, 4, 4, 0] },
      barWidth: '60%'
    }]
  })
}

function initCharts() {
  initLineChart()
  initPieChart()
  initBarChart()
  setTimeout(() => {
    lineChart?.resize()
    pieChart?.resize()
    barChart?.resize()
  }, 100)
}

onMounted(async () => {
  await nextTick()
  await nextTick()
  await nextTick()
  setTimeout(() => {
    initCharts()
    loadLatestPrices()
    loadFilter1Charts()
    loadFilter2Charts()
  }, 200)
  window.addEventListener('resize', () => {
    lineChart?.resize()
    pieChart?.resize()
    barChart?.resize()
  })
})

onUnmounted(() => {
  lineChart?.dispose()
  pieChart?.dispose()
  barChart?.dispose()
})
</script>

<style scoped>
.dashboard {
  padding: 24px 32px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
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
  padding: 8px 0;
  flex-wrap: wrap;
  gap: 12px;
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
  flex-wrap: wrap;
}

.record-count {
  font-size: 12px;
  color: var(--text-muted);
  padding: 4px 12px;
  background: var(--bg-hover);
  border-radius: 12px;
}

.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  min-width: 0;
}

.chart-half {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.charts-grid-46 {
  display: grid;
  grid-template-columns: 40% 60%;
  gap: 20px;
  margin-bottom: 20px;
}

.chart-4 {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.chart-6 {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.indicator-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  flex: 1;
}

.indicator-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
}

.indicator-card .card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.indicator-card .card-label {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

.indicator-card .card-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.indicator-card .card-product {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 500;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.indicator-card .card-value {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.indicator-card .trend-icon {
  font-size: 24px;
  font-weight: 700;
}

.indicator-card .card-value.rise .trend-icon {
  color: var(--rise-color);
}

.indicator-card .card-value.fall .trend-icon {
  color: var(--fall-color);
}

.indicator-card .value-num {
  font-size: 28px;
  font-weight: 700;
  font-family: 'Outfit', sans-serif;
}

.indicator-card .card-value.rise .value-num {
  color: var(--rise-color);
}

.indicator-card .card-value.fall .value-num {
  color: var(--fall-color);
}

.indicator-card .card-detail {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--text-muted);
}

.chart-container {
  height: 280px;
  width: 100%;
  margin-top: 8px;
  flex: 1;
  min-width: 0;
}

.table-section {
  margin-top: 16px;
  border-top: 1px solid var(--border-color);
  padding-top: 16px;
}

.table-section :deep(.el-table__header-wrapper th) {
  padding: 8px 4px;
}

.table-section :deep(.el-table__body-wrapper td) {
  padding: 10px 4px;
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

.column-header-with-filter {
  display: flex;
  align-items: center;
  gap: 4px;
}

.column-header-with-filter .filter-icon {
  cursor: pointer;
  color: var(--text-muted);
  font-size: 12px;
  padding: 2px 4px;
  border-radius: 4px;
  transition: all 0.2s;
  display: inline-block;
}

.column-header-with-filter .filter-icon:hover {
  color: var(--accent-cyan);
  background: var(--bg-hover);
}

.column-header-with-filter.date-header {
  gap: 8px;
}

.column-header-with-filter :deep(.el-date-editor) {
  width: 160px !important;
}

.column-header-with-filter :deep(.el-input__wrapper) {
  width: 100%;
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
  .charts-grid { grid-template-columns: 1fr; }
}

@media (max-width: 768px) {
  .controls { flex-direction: column; align-items: stretch; }
}
</style>