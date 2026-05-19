<template>
  <div class="dashboard">
    <div class="dashboard-container">
      <!-- 第一张卡片：筛选器1 + 折线图 + 柱状图 -->
      <el-card class="chart-card animate-in" style="animation-delay: 0.05s">
        <template #header>
          <div class="card-header">
            <div class="header-title">
              <div class="title-icon-wrapper">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                </svg>
              </div>
              <span>价格分析</span>
            </div>
            <div class="controls">
              <SourceSelector v-model="filter1Source" />
              <IndustrySelector v-model="filter1Industry" />
              <CategorySelector
                v-model="filter1CategoryId"
                v-model:subcategoryValue="filter1SubcategoryId"
                :industry="filter1Industry"
                @change="handleFilter1Change"
              />
              <el-date-picker
                v-model="filter1DateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始"
                end-placeholder="结束"
                size="small"
                style="width: 180px"
                @change="handleFilter1Change"
              />
              <el-select v-model="compareDays" placeholder="时间范围" size="small" style="width: 72px" @change="loadFilter1Charts">
                <el-option label="7天" :value="7" />
                <el-option label="30天" :value="30" />
                <el-option label="90天" :value="90" />
              </el-select>
            </div>
          </div>
        </template>
        <div class="charts-grid">
          <div class="chart-half">
            <div class="chart-title">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
                <polyline points="17 6 23 6 23 12"/>
              </svg>
              <span>价格走势</span>
            </div>
            <div class="chart-wrapper">
              <div ref="lineChartRef" class="chart-container" style="height: 260px; width: 100%;"></div>
              <div class="chart-actions" @mouseenter="hoverChart = 'line'" @mouseleave="hoverChart = null">
                <button class="chart-action-btn" title="详情" @click="showChartDetail('line')">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                  </svg>
                </button>
                <button class="chart-action-btn" title="下载" @click="downloadChart('line')">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="7 10 12 15 17 10"/>
                    <line x1="12" y1="15" x2="12" y2="3"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
          <div class="chart-half">
            <div class="chart-title">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="20" x2="18" y2="10"/>
                <line x1="12" y1="20" x2="12" y2="4"/>
                <line x1="6" y1="20" x2="6" y2="14"/>
              </svg>
              <span>涨跌排行 TOP10</span>
            </div>
            <div class="chart-wrapper">
              <div ref="barChartRef" class="chart-container" style="height: 260px; width: 100%;"></div>
              <div class="chart-actions" @mouseenter="hoverChart = 'bar'" @mouseleave="hoverChart = null">
                <button class="chart-action-btn" title="详情" @click="showChartDetail('bar')">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                  </svg>
                </button>
                <button class="chart-action-btn" title="下载" @click="downloadChart('bar')">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="7 10 12 15 17 10"/>
                    <line x1="12" y1="15" x2="12" y2="3"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 第二张卡片：筛选器2 + 饼图 + 关键指标 -->
      <el-card class="chart-card animate-in" style="animation-delay: 0.1s">
        <template #header>
          <div class="card-header">
            <div class="header-title">
              <div class="title-icon-wrapper">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21.21 15.89A10 10 0 1 1 8 2.83"/>
                  <path d="M22 12A10 10 0 0 0 12 2v10z"/>
                </svg>
              </div>
              <span>价格分布与关键指标</span>
            </div>
            <div class="controls">
              <SourceSelector v-model="filter2Source" />
              <IndustrySelector v-model="filter2Industry" />
              <CategorySelector
                v-model="filter2CategoryId"
                v-model:subcategoryValue="filter2SubcategoryId"
                :industry="filter2Industry"
                @change="handleFilter2Change"
              />
              <el-date-picker
                v-model="filter2DateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始"
                end-placeholder="结束"
                size="small"
                style="width: 180px"
                @change="handleFilter2Change"
              />
            </div>
          </div>
        </template>
        <div class="charts-grid-46">
          <div class="chart-4">
            <div class="chart-wrapper" style="width:100%;height:100%;min-height:240px;position:relative;">
              <div ref="pieChartRef" class="pie-chart" style="width:100%;height:100%;min-height:240px;"></div>
              <div class="chart-actions" @mouseenter="hoverChart = 'pie'" @mouseleave="hoverChart = null">
                <button class="chart-action-btn" title="详情" @click="showChartDetail('pie')">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                  </svg>
                </button>
                <button class="chart-action-btn" title="下载" @click="downloadChart('pie')">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="7 10 12 15 17 10"/>
                    <line x1="12" y1="15" x2="12" y2="3"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
          <div class="chart-6">
            <div class="indicator-cards">
              <div class="indicator-card" v-for="(card, idx) in indicatorCards" :key="card.type" :style="{animationDelay: `${0.15 + idx * 0.05}s`}">
                <div class="card-header-row">
                  <span class="card-label">{{ card.type }}</span>
                  <el-select v-model="card.selected" placeholder="同比/环比" size="small" style="width: 90px">
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

      <div class="ranking-row" v-if="rankingData.rising.length || rankingData.falling.length">
        <el-card class="ranking-card animate-in" style="animation-delay: 0.2s">
          <template #header>
            <div class="card-header">
              <div class="header-title rising">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
                  <polyline points="17 6 23 6 23 12"/>
                </svg>
                <span>涨幅榜</span>
              </div>
            </div>
          </template>
          <div class="ranking-list">
            <div v-for="(item, index) in rankingData.rising" :key="index" class="ranking-item rising">
              <span class="rank-num">{{ index + 1 }}</span>
              <span class="rank-name">{{ item.product_name }}</span>
              <span class="rank-price">¥{{ item.latest_price?.toLocaleString() }}</span>
              <span class="rank-change rise">+{{ item.change_percent }}%</span>
            </div>
          </div>
        </el-card>

        <el-card class="ranking-card animate-in" style="animation-delay: 0.25s">
          <template #header>
            <div class="card-header">
              <div class="header-title falling">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/>
                  <polyline points="17 18 23 18 23 12"/>
                </svg>
                <span>跌幅榜</span>
              </div>
            </div>
          </template>
          <div class="ranking-list">
            <div v-for="(item, index) in rankingData.falling" :key="index" class="ranking-item falling">
              <span class="rank-num">{{ index + 1 }}</span>
              <span class="rank-name">{{ item.product_name }}</span>
              <span class="rank-price">¥{{ item.latest_price?.toLocaleString() }}</span>
              <span class="rank-change fall">{{ item.change_percent }}%</span>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 第三张卡片：详细数据表格 -->
      <el-card class="chart-card animate-in" style="animation-delay: 0.3s">
        <template #header>
          <div class="card-header">
            <div class="header-title">
              <div class="title-icon-wrapper">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                </svg>
              </div>
              <span>详细数据</span>
            </div>
            <div class="controls">
              <SourceSelector v-model="filter3Source" />
              <IndustrySelector v-model="filter3Industry" />
              <CategorySelector
                v-model="filter3CategoryId"
                v-model:subcategoryValue="filter3SubcategoryId"
                :industry="filter3Industry"
                @change="handleFilter3Change"
              />
              <el-input
                v-model="searchKeyword"
                placeholder="搜索产品/数据源"
                size="small"
                clearable
                style="width: 160px"
              />
              <span class="record-count">{{ filteredAndSortedData.length }} 条记录</span>
            </div>
          </div>
        </template>

        <div class="table-section">
          <el-table
            :data="paginatedData"
            style="width: 100%"
            size="small"
            row-key="product_id"
            :expand-row-keys="expandedRows"
            @expand-change="handleExpandChange"
            :default-sort="{ prop: 'latest_date', order: 'descending' }"
            class="data-table"
          >
            <el-table-column type="expand" width="48">
              <template #default="{ row }">
                <div class="expand-content">
                  <p class="expand-title">历史价格记录</p>
                  <div ref="historyChartRef" class="history-sparkline"></div>
                  <el-table :data="paginatedHistoryData" size="small" class="detail-table">
                    <el-table-column prop="record_date" label="日期" width="120" />
                    <el-table-column prop="price" label="价格" width="120">
                      <template #default="{ row: detail }">
                        <span class="price-value">¥{{ detail.price.toLocaleString() }}</span>
                      </template>
                    </el-table-column>
                    <el-table-column prop="trend" label="趋势" width="80">
                      <template #default="{ row: detail }">
                        <span :class="['trend-badge', detail.trend]">
                          {{ detail.trend === '涨' ? '↑' : detail.trend === '跌' ? '↓' : '—' }}
                        </span>
                      </template>
                    </el-table-column>
                    <el-table-column prop="change_percent" label="较昨日涨跌幅" width="100">
                      <template #default="{ row: detail }">
                        <span :class="detail.change_percent > 0 ? 'text-rise' : detail.change_percent < 0 ? 'text-fall' : 'text-flat'">
                          {{ detail.change_percent > 0 ? '+' : '' }}{{ detail.change_percent }}%
                        </span>
                      </template>
                    </el-table-column>
                    <el-table-column prop="region" label="地区" width="100" />
                    <el-table-column prop="supplier" label="供应商" show-overflow-tooltip />
                    <el-table-column prop="source" label="数据源" width="100" />
                  </el-table>
                  <el-pagination
                    v-if="expandedRows.length > 0 && latestPrices.find(p => p.product_id === expandedRows[0])?.history?.length > 0"
                    background
                    size="small"
                    layout="sizes, prev, pager, next"
                    :total="latestPrices.find(p => p.product_id === expandedRows[0])?.history?.length || 0"
                    :page-size="historyPagination.pageSize"
                    :page-sizes="[10, 20, 50, 100]"
                    :current-page="historyPagination.page"
                    @size-change="handleHistorySizeChange"
                    @current-change="handleHistoryPageChange"
                    style="margin-top: 10px; justify-content: center"
                  />
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="product_name" label="产品名称" min-width="150" />
            <el-table-column prop="price" label="最新价格" width="130">
              <template #default="{ row }">
                <span class="price-value">¥{{ row.price?.toLocaleString() }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="change_percent" label="较昨日涨跌幅" width="100">
              <template #default="{ row }">
                <span :class="row.change_percent > 0 ? 'text-rise' : row.change_percent < 0 ? 'text-fall' : 'text-flat'">
                  {{ row.change_percent > 0 ? '+' : '' }}{{ row.change_percent }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="trend" label="趋势" width="80">
              <template #default="{ row }">
                <span :class="['trend-badge', row.trend]">
                  {{ row.trend === '涨' ? '↑' : row.trend === '跌' ? '↓' : '—' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="latest_date" label="最新日期" width="120" />
            <el-table-column prop="source" label="数据源" width="100" />
          </el-table>
          <el-pagination
            v-if="filteredAndSortedData.length > 0"
            background
            layout="sizes, prev, pager, next"
            :total="filteredAndSortedData.length"
            :page-size="pagination.pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :current-page="pagination.page"
            @size-change="handleSizeChange"
            @current-change="handlePageChange"
            style="margin-top: 20px; justify-content: center"
          />
        </div>
      </el-card>
    </div>

    <!-- 图表详情弹窗 -->
    <el-dialog v-model="chartDetailVisible" :title="chartDetailTitle" width="680px" :close-on-click-modal="true">
      <el-table v-if="chartDetailData.length > 0" :data="chartDetailData" border size="small" max-height="400">
        <el-table-column v-for="col in chartDetailColumns" :key="col.prop" :prop="col.prop" :label="col.label" :width="col.width" />
      </el-table>
      <div v-else style="text-align:center;color:#999;padding:40px;">暂无数据</div>
      <template #footer>
        <el-button @click="chartDetailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { priceApi } from '../api/price'
import * as echarts from 'echarts'
import CategorySelector from '../components/CategorySelector.vue'
import SourceSelector from '../components/SourceSelector.vue'
import IndustrySelector from '../components/IndustrySelector.vue'

const lineChartRef = ref(null)
const pieChartRef = ref(null)
const barChartRef = ref(null)
const historyChartRef = ref(null)

const hoverChart = ref(null)
const chartDetailVisible = ref(false)
const chartDetailTitle = ref('')
const chartDetailData = ref([])
const chartDetailColumns = ref([])

const lineChartRawData = ref({ dates: [], series: [] })
const barChartRawData = ref({ categories: [], values: [] })
const pieChartRawData = ref({ labels: [], sizes: [] })

const latestPrices = ref([])
const expandedRows = ref([])
const rankingData = ref({ rising: [], falling: [] })

const filter1CategoryId = ref(null)
const filter1SubcategoryId = ref(null)
const filter1DateRange = ref([])
const filter1Source = ref(null)
const filter1Industry = ref(null)

watch(filter1Source, () => { loadFilter1Charts() })
watch(filter1Industry, () => { loadFilter1Charts() })

const filter2CategoryId = ref(null)
const filter2SubcategoryId = ref(null)
const filter2DateRange = ref([])
const filter2Source = ref(null)
const filter2Industry = ref(null)

watch(filter2Source, () => { loadFilter2Charts() })
watch(filter2Industry, () => { loadFilter2Charts() })

const filter3CategoryId = ref(null)
const filter3SubcategoryId = ref(null)
const filter3Source = ref(null)
const filter3Industry = ref(null)
const searchKeyword = ref('')

watch(filter3Source, () => { handleFilter3Change() })
watch(filter3Industry, () => { handleFilter3Change() })

const pagination = ref({ page: 1, pageSize: 10, total: 0 })
const historyPagination = ref({ page: 1, pageSize: 10 })
const compareDays = ref(7)

const indicatorCards = ref([
  { type: '较昨日同比最高', selected: 'yoy', productName: '-', changePercent: 0, trend: 'rise', price: 0 },
  { type: '较昨日环比最高', selected: 'qoq', productName: '-', changePercent: 0, trend: 'rise', price: 0 }
])

let lineChart = null
let pieChart = null
let barChart = null
let historyChart = null
let searchTimer = null

async function loadLatestPrices() {
  try {
    const params = {
      category_id: filter3CategoryId.value || null,
      subcategory_id: filter3SubcategoryId.value || null,
      source: filter3Source.value || null,
      industry: filter3Industry.value || null
    }
    const res = await priceApi.getLatestPrices(params)
    latestPrices.value = (res.data.data || []).map(p => ({ ...p, history: [] }))
    pagination.value.total = res.data.total || 0
  } catch (e) {
    console.error('Failed to load prices', e)
  }
}

function handlePageChange(page) {
  pagination.value.page = page
}

function handleSizeChange(size) {
  pagination.value.pageSize = size
  pagination.value.page = 1
}

const filteredAndSortedData = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  if (!keyword) return [...latestPrices.value]
  return [...latestPrices.value].filter(p =>
    (p.product_name || '').toLowerCase().includes(keyword) ||
    (p.source || '').toLowerCase().includes(keyword)
  )
})

const paginatedData = computed(() => {
  const start = (pagination.value.page - 1) * pagination.value.pageSize
  const end = start + pagination.value.pageSize
  return filteredAndSortedData.value.slice(start, end)
})

const paginatedHistoryData = computed(() => {
  if (!expandedRows.value.length) return []
  const expandedId = expandedRows.value[0]
  const row = latestPrices.value.find(p => p.product_id === expandedId)
  if (!row || !row.history || row.history.length === 0) return []
  const start = (historyPagination.value.page - 1) * historyPagination.value.pageSize
  const end = start + historyPagination.value.pageSize
  return row.history.slice(start, end)
})

watch(paginatedHistoryData, () => { nextTick(() => updateHistoryChart()) }, { deep: true })

async function handleExpandChange(row) {
  const id = row.product_id
  if (expandedRows.value.includes(id)) {
    expandedRows.value = []
  } else {
    expandedRows.value = [id]
    historyPagination.value.page = 1
    if (historyChart) {
      historyChart.clear()
    }
    nextTick(() => {
      initHistoryChart()
    })
    if (!row.history || row.history.length === 0) {
      try {
        const res = await priceApi.getPriceHistory(id, 365, filter3Source.value)
        const historyData = res.data || []
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

function handleHistoryPageChange(page) {
  historyPagination.value.page = page
}

function handleHistorySizeChange(size) {
  historyPagination.value.pageSize = size
  historyPagination.value.page = 1
}

function handleFilter1Change() {
  loadFilter1Charts()
}

function handleFilter2Change() {
  loadFilter2Charts()
}

function handleFilter3Change() {
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
    let days = 30
    if (filter2DateRange.value && filter2DateRange.value.length === 2) {
      const start = new Date(filter2DateRange.value[0])
      const end = new Date(filter2DateRange.value[1])
      days = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1
    }

    const params = {
      days: days,
      category_id: filter2CategoryId.value || null,
      subcategory_id: filter2SubcategoryId.value || null,
      source: filter2Source.value || null,
      industry: filter2Industry.value || null
    }
    const res = await priceApi.getDashboardRanking(params)
    const rising = res.data.rising || []

    if (rising.length > 0) {
      const top1 = rising[0]
      indicatorCards.value[0] = {
        type: '较昨日同比最高',
        selected: 'yoy',
        productName: top1.product_name,
        changePercent: Math.abs(top1.change_percent),
        trend: top1.change_percent >= 0 ? 'rise' : 'fall',
        price: top1.latest_price || 0
      }
    }

    if (rising.length > 1) {
      const top2 = rising[1]
      indicatorCards.value[1] = {
        type: '较昨日环比最高',
        selected: 'qoq',
        productName: top2.product_name,
        changePercent: Math.abs(top2.change_percent),
        trend: top2.change_percent >= 0 ? 'rise' : 'fall',
        price: top2.latest_price || 0
      }
    } else if (rising.length === 1) {
      const top1 = rising[0]
      indicatorCards.value[1] = {
        type: '较昨日环比最高',
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
    let days = compareDays.value
    if (filter1DateRange.value && filter1DateRange.value.length === 2) {
      const start = new Date(filter1DateRange.value[0])
      const end = new Date(filter1DateRange.value[1])
      days = Math.max(7, Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1)
    }

    const res = await priceApi.getDashboardHistoryCompare(
      null,
      days,
      filter1CategoryId.value || null,
      filter1SubcategoryId.value || null,
      filter1Source.value || null,
      filter1Industry.value || null
    )

    if (!res.data || !res.data.dates || res.data.dates.length === 0) {
      lineChart.setOption({ series: [] })
      lineChartRawData.value = { dates: [], series: [] }
      return
    }

    const { dates, series } = res.data
    lineChartRawData.value = { dates, series }
    const lineColors = ['#E63946', '#2A9D5C', '#E9C46A', '#264653', '#F4A261', '#8E44AD', '#1ABC9C', '#E74C3C', '#3498DB', '#9B59B6']

    lineChart.setOption({
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#fff',
        borderColor: '#E8E3F3',
        borderWidth: 1,
        textStyle: { color: '#1E293B', fontSize: 12 },
        borderRadius: 8,
        boxShadow: '0 2px 8px rgba(139, 92, 246, 0.08)',
        formatter: (params) => {
          const date = params[0].axisValue
          let html = `<strong style="color: #1E293B">${date}</strong><br/>`
          params.forEach(p => {
            html += `<span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: ${p.color}; margin-right: 6px;"></span>${p.seriesName}: <strong style="color: #8B5CF6">¥${p.value?.toLocaleString() ?? '-'}</strong><br/>`
          })
          return html
        }
      },
      legend: {
        show: true,
        bottom: 0,
        textStyle: { color: '#64748B', fontSize: 11 },
        type: 'scroll',
        pageTextStyle: { color: '#64748B' }
      },
      grid: { left: 60, right: 30, bottom: 40, top: 20, containLabel: true },
      xAxis: {
        type: 'category',
        data: dates,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#94A3B4', fontSize: 11 }
      },
      yAxis: {
        type: 'value',
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#94A3B4', fontSize: 11, formatter: val => `¥${val.toLocaleString()}` },
        splitLine: { lineStyle: { color: '#F0EBF9', type: 'dashed' } }
      },
      series: series.map((s, i) => ({
        name: s.name,
        type: 'line',
        data: s.data,
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { width: 2.5, color: lineColors[i % lineColors.length] },
        itemStyle: { color: lineColors[i % lineColors.length] },
        emphasis: {
          focus: 'series',
          itemStyle: { borderColor: '#fff', borderWidth: 2, shadowBlur: 8, shadowColor: 'rgba(139, 92, 246, 0.3)' }
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
      subcategory_id: filter1SubcategoryId.value || null,
      source: filter1Source.value || null,
      industry: filter1Industry.value || null
    }
    const res = await priceApi.getDashboardRanking(params)
    const rising = res.data.rising || []
    const falling = res.data.falling || []
    rankingData.value = { rising, falling }
    barChartRawData.value = {
      categories: rising.map(r => r.product_name),
      values: rising.map(r => r.change_percent),
      fullData: rising
    }
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
      subcategory_id: filter2SubcategoryId.value || null,
      source: filter2Source.value || null,
      industry: filter2Industry.value || null
    }
    const res = await priceApi.getDashboardDistribution(params)
    if (res.data.labels && res.data.labels.length > 0) {
      pieChartRawData.value = {
        labels: res.data.labels,
        sizes: res.data.sizes
      }
      const pieColors = ['#0077cc', '#00a8e8', '#4db8e8', '#005fa3', '#003d6b', '#006594', '#0077cc', '#00a8e8', '#e91e63', '#6739b6']
      pieChart.setOption({
        tooltip: {
          trigger: 'item',
          formatter: (params) => `<strong>${params.name}</strong><br/>价格: ¥${params.value?.toLocaleString() ?? '-'}<br/>占比: ${params.percent}%`,
          backgroundColor: '#ffffff',
          borderColor: '#E8E3F3',
          borderWidth: 1,
          textStyle: { color: '#1E293B' },
          borderRadius: 8
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

function showChartDetail(type) {
  if (type === 'line') {
    chartDetailTitle.value = '价格走势 - 详细数据'
    const { dates, series } = lineChartRawData.value
    if (!dates || dates.length === 0) {
      chartDetailData.value = []
      chartDetailColumns.value = []
    } else {
      const cols = [{ prop: 'date', label: '日期', width: 120 }]
      series.forEach((s, i) => cols.push({ prop: `series${i}`, label: s.name || `产品${i + 1}`, width: 140 }))
      const rows = dates.map((d, di) => {
        const row = { date: d }
        series.forEach((s, si) => { row[`series${si}`] = s.data[di] != null ? `¥${s.data[di].toLocaleString()}` : '-' })
        return row
      })
      chartDetailData.value = rows
      chartDetailColumns.value = cols
    }
  } else if (type === 'bar') {
    chartDetailTitle.value = '涨跌排行 TOP10 - 详细数据'
    const { fullData } = barChartRawData.value
    if (!fullData || fullData.length === 0) {
      chartDetailData.value = []
      chartDetailColumns.value = []
    } else {
      chartDetailColumns.value = [
        { prop: 'product_name', label: '产品名称', width: 180 },
        { prop: 'change_percent', label: '涨跌幅', width: 120 },
        { prop: 'latest_price', label: '最新价格', width: 120 },
        { prop: 'avg_price', label: '平均价格', width: 120 }
      ]
      chartDetailData.value = fullData.map(r => ({
        product_name: r.product_name,
        change_percent: `${r.change_percent > 0 ? '+' : ''}${r.change_percent}%`,
        latest_price: r.latest_price != null ? `¥${r.latest_price.toLocaleString()}` : '-',
        avg_price: r.avg_price != null ? `¥${r.avg_price.toLocaleString()}` : '-'
      }))
    }
  } else if (type === 'pie') {
    chartDetailTitle.value = '价格分布 - 详细数据'
    const { labels, sizes } = pieChartRawData.value
    if (!labels || labels.length === 0) {
      chartDetailData.value = []
      chartDetailColumns.value = []
    } else {
      const total = (sizes || []).reduce((s, v) => s + v, 0)
      chartDetailColumns.value = [
        { prop: 'product_name', label: '产品名称', width: 200 },
        { prop: 'price', label: '价格', width: 140 },
        { prop: 'percent', label: '占比', width: 120 }
      ]
      chartDetailData.value = labels.map((l, i) => ({
        product_name: l,
        price: sizes[i] != null ? `¥${sizes[i].toLocaleString()}` : '-',
        percent: total > 0 ? `${((sizes[i] / total) * 100).toFixed(2)}%` : '-'
      }))
    }
  }
  chartDetailVisible.value = true
}

function downloadChart(type) {
  let chartInstance = null
  let filename = ''
  if (type === 'line') {
    chartInstance = lineChart
    filename = '价格走势'
  } else if (type === 'bar') {
    chartInstance = barChart
    filename = '涨跌排行'
  } else if (type === 'pie') {
    chartInstance = pieChart
    filename = '价格分布'
  }
  if (!chartInstance) return
  const url = chartInstance.getDataURL({ type: 'png', pixelRatio: 2, backgroundColor: '#fff' })
  const link = document.createElement('a')
  link.download = `${filename}_${new Date().toISOString().slice(0, 10)}.png`
  link.href = url
  link.click()
}

function initLineChart() {
  if (!lineChartRef.value) return
  if (lineChart) {
    lineChart.dispose()
  }
  lineChart = echarts.init(lineChartRef.value)
  lineChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: '#E8E3F3', textStyle: { color: '#1E293B', fontSize: 12 } },
    legend: { show: true, bottom: 0, textStyle: { color: '#64748B', fontSize: 11 }, type: 'scroll', pageTextStyle: { color: '#64748B' } },
    grid: { left: 60, right: 30, bottom: 40, top: 20, containLabel: true },
    xAxis: { type: 'category', data: [], axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#94A3B4', fontSize: 11 } },
    yAxis: { type: 'value', axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#94A3B4', fontSize: 11, formatter: val => `¥${val.toLocaleString()}` }, splitLine: { lineStyle: { color: '#F0EBF9', type: 'dashed' } } },
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
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)', backgroundColor: '#ffffff', borderColor: '#E8E3F3', textStyle: { color: '#1E293B' } },
    legend: { orient: 'vertical', left: 'left', top: 'center', textStyle: { color: '#64748B', fontSize: 11 }, itemGap: 8, width: 80 },
    series: [{
      type: 'pie',
      radius: ['28%', '60%'],
      center: ['55%', '50%'],
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
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: '#ffffff', borderColor: '#E8E3F3', textStyle: { color: '#1E293B' }, axisPointer: { type: 'shadow' }, borderRadius: 8 },
    grid: { left: '3%', right: '8%', bottom: '3%', top: '3%', containLabel: true },
    xAxis: { type: 'value', axisLine: { show: false }, axisLabel: { color: '#94A3B4' }, splitLine: { lineStyle: { color: '#F0EBF9', type: 'dashed' } } },
    yAxis: { type: 'category', data: [], axisLine: { lineStyle: { color: '#E8E3F3' } }, axisLabel: { color: '#64748B', fontSize: 10 } },
    series: [{
      type: 'bar',
      itemStyle: { color: (params) => params.value >= 0 ? '#E63946' : '#2A9D5C', borderRadius: [0, 4, 4, 0] },
      barWidth: '60%'
    }]
  })
}

function initHistoryChart() {
  if (!historyChartRef.value) return
  if (historyChart) {
    historyChart.dispose()
  }
  historyChart = echarts.init(historyChartRef.value)
  historyChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: '#E8E3F3', textStyle: { color: '#1E293B', fontSize: 11 }, axisPointer: { type: 'line' } },
    grid: { left: 50, right: 20, bottom: 20, top: 10, containLabel: true },
    xAxis: { type: 'category', data: [], axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#94A3B8', fontSize: 10, rotate: 30 } },
    yAxis: { type: 'value', axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#94A3B8', fontSize: 10, formatter: val => `¥${val.toLocaleString()}` }, splitLine: { lineStyle: { color: '#F0EBF9', type: 'dashed' } } },
    series: [{
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: { color: '#7C3AED', width: 2 },
      itemStyle: { color: '#7C3AED' },
      areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(124,58,237,0.25)' }, { offset: 1, color: 'rgba(124,58,237,0.02)' }] } }
    }]
  })
}

function updateHistoryChart() {
  if (!historyChart || !historyChartRef.value) return
  const data = paginatedHistoryData.value
  if (!data || data.length === 0) return
  const dates = data.map(d => d.record_date)
  const prices = data.map(d => d.price)
  historyChart.setOption({
    xAxis: { data: dates },
    series: [{ data: prices }]
  })
}

function initCharts() {
  initLineChart()
  initPieChart()
  initBarChart()
  initHistoryChart()
  setTimeout(() => {
    lineChart?.resize()
    pieChart?.resize()
    barChart?.resize()
    historyChart?.resize()
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
    historyChart?.resize()
  })
})

onUnmounted(() => {
  lineChart?.dispose()
  pieChart?.dispose()
  barChart?.dispose()
  historyChart?.dispose()
})
</script>

<style scoped>
.dashboard {
  padding: 24px;
  min-height: 100vh;
}

.dashboard-container {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.chart-card {
  border-radius: 16px !important;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  flex-wrap: wrap;
  gap: 16px;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-family: 'Fira Sans', sans-serif;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.title-icon-wrapper {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: var(--color-primary-dim);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
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
  font-weight: 500;
}

.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  min-width: 0;
}

.chart-half {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.chart-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 12px;
  padding-left: 4px;
}

.chart-title svg {
  color: var(--color-primary);
}

.charts-grid-46 {
  display: flex;
  gap: 24px;
  align-items: stretch;
}

.chart-4 {
  flex: 0 0 45%;
  display: flex;
  align-items: stretch;
}

.chart-6 {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.pie-chart {
  width: 100%;
  height: 100%;
  min-height: 240px;
}

.chart-title {
  display: none;
}

.indicator-cards {
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
}

.indicator-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 16px;
  flex: 1;
  display: flex;
  flex-direction: column;
  opacity: 0;
  animation: fadeInUp 0.4s ease-out forwards;
}

.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.card-label {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.card-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.card-product {
  font-size: 13px;
  color: var(--text-primary);
  font-weight: 500;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-value {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.trend-icon {
  font-size: 22px;
  font-weight: 700;
}

.card-value.rise .trend-icon {
  color: var(--rise-color);
}

.card-value.fall .trend-icon {
  color: var(--fall-color);
}

.value-num {
  font-size: 26px;
  font-weight: 700;
  font-family: 'Fira Sans', sans-serif;
}

.card-value.rise .value-num {
  color: var(--rise-color);
}

.card-value.fall .value-num {
  color: var(--fall-color);
}

.card-detail {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--text-muted);
}

.chart-container {
  height: 260px;
  width: 100%;
  margin-top: 8px;
  flex: 1;
  min-width: 0;
}

.chart-wrapper {
  position: relative;
  flex: 1;
  min-width: 0;
}

.chart-actions {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s ease;
  z-index: 10;
}

.chart-wrapper:hover .chart-actions {
  opacity: 1;
}

.chart-action-btn {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(4px);
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
  padding: 0;
}

.chart-action-btn:hover {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: #fff;
}

.table-section {
  margin-top: 16px;
  border-top: 1px solid var(--border-color);
  padding-top: 16px;
}

.table-section :deep(.el-table__header-wrapper th) {
  padding: 10px 4px;
  font-size: 11px !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.table-section :deep(.el-table__body-wrapper td) {
  padding: 12px 4px;
}

.price-value {
  font-family: 'Fira Code', monospace;
  font-weight: 600;
  color: var(--color-primary);
  font-size: 13px;
}

.trend-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 22px;
  padding: 0 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.trend-badge.涨 { background: rgba(230, 57, 70, 0.12); color: var(--rise-color); }
.trend-badge.跌 { background: rgba(42, 157, 92, 0.12); color: var(--fall-color); }
.trend-badge.平 {background: rgba(100, 116, 139, 0.12); color: var(--text-secondary); }

.expand-content {
  padding: 12px 16px;
  background: var(--bg-primary);
  border-radius: 12px;
  margin: 8px 0;
}

.history-sparkline {
  height: 140px;
  margin-bottom: 12px;
}

.expand-title {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 12px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-table {
  background: transparent !important;
}

.text-rise { color: var(--rise-color); font-weight: 500; }
.text-fall { color: var(--fall-color); font-weight: 500; }
.text-flat { color: var(--text-secondary); }

.ranking-row {
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

.header-title.rising {
  color: var(--rise-color);
}

.header-title.falling {
  color: var(--fall-color);
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

@media (max-width: 1200px) {
  .charts-grid { grid-template-columns: 1fr; }
  .charts-grid-46 { flex-direction: column; }
  .chart-4 { flex: none; width: 100%; }
}

@media (max-width: 768px) {
  .controls { flex-direction: column; align-items: stretch; }
  .dashboard { padding: 16px; }
}
</style>