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

              <el-date-picker
                v-model="filter1DateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始"
                end-placeholder="结束"
                size="small"
                style="width: 180px"
                
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

              <el-date-picker
                v-model="filter2DateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始"
                end-placeholder="结束"
                size="small"
                style="width: 180px"
                
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
              <div class="indicator-card" v-for="(card, idx) in indicatorCards" :key="card.metricType" :style="{animationDelay: `${0.15 + idx * 0.05}s`}">
                <div class="card-header-row">
                  <span class="card-placeholder"></span>
                  <el-select v-model="card.metricType" size="small" style="width: 80px" @change="onMetricTypeChange(idx)">
                    <el-option label="同比" value="yoy" />
                    <el-option label="环比" value="qoq" />
                    <el-option label="7日涨跌" value="d7" />
                    <el-option label="30日涨跌" value="d30" />
                  </el-select>
                </div>
                <div class="card-body" :class="{ 'no-data': !card.hasData }">
                  <div class="card-main">
                    <div class="card-product">{{ card.productName }}</div>
                    <div class="card-value" :class="card.trend">
                      <span class="trend-icon">{{ card.trend === 'rise' ? '↑' : '↓' }}</span>
                      <span class="value-num">{{ card.changePercent }}%</span>
                    </div>
                  </div>
                  <div class="card-price">¥{{ card.price?.toLocaleString() }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 第三张卡片：供应商对比 -->
      <el-card class="chart-card animate-in" style="animation-delay: 0.2s">
        <template #header>
          <div class="card-header">
            <div class="header-title">
              <div class="title-icon-wrapper">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                  <circle cx="9" cy="7" r="4"/>
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                  <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
              </div>
              <span>供应商对比</span>
            </div>
            <div class="controls">
              <el-select
                v-model="selectedSupplierProduct"
                clearable
                placeholder="选择产品（可选）"
                size="small"
                style="width: 160px"
                @change="loadSupplierComparison"
              >
                <el-option
                  v-for="p in latestPrices"
                  :key="p.product_id"
                  :label="p.product_name"
                  :value="p.product_id"
                />
              </el-select>
              <el-select v-model="supplierComparisonDays" size="small" style="width: 72px" @change="loadSupplierComparison">
                <el-option label="7天" :value="7" />
                <el-option label="30天" :value="30" />
                <el-option label="90天" :value="90" />
              </el-select>
            </div>
          </div>
        </template>
        <div class="charts-grid-46">
          <div class="chart-4">
            <div class="chart-wrapper" style="width:100%;height:100%;min-height:220px;position:relative;">
              <div ref="supplierChartRef" class="pie-chart" style="width:100%;height:100%;min-height:220px;"></div>
            </div>
          </div>
          <div class="chart-6">
            <div class="chart-wrapper" style="width:100%;height:100%;min-height:220px;position:relative;">
              <div ref="supplierBarChartRef" style="width:100%;height:100%;min-height:220px;"></div>
            </div>
          </div>
        </div>
        <div class="supplier-table" v-if="supplierProducts.length > 0">
          <p class="expand-title" style="margin-top: 12px;">供应商-产品明细</p>
          <el-table :data="supplierProducts" size="small" style="width: 100%;" row-key="supplier">
            <el-table-column prop="supplier" label="供应商" min-width="120" />
            <el-table-column label="产品数" min-width="80">
              <template #default="{ row }">{{ row.products.length }}个</template>
            </el-table-column>
            <el-table-column label="报价条数" min-width="100">
              <template #default="{ row }">{{ row.products.reduce((s, p) => s + p.count, 0) }}条</template>
            </el-table-column>
            <el-table-column label="最高报价" min-width="120">
              <template #default="{ row }">
                <span class="price-value">¥{{ row.products.length > 0 ? Math.max(...row.products.map(p => p.price)).toLocaleString() : '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="最低报价" min-width="120">
              <template #default="{ row }">
                <span class="price-value">¥{{ row.products.length > 0 ? Math.min(...row.products.map(p => p.price)).toLocaleString() : '-' }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
        <div v-else class="no-detail-data" style="padding: 24px; text-align: center; color: #999;">
          暂无供应商数据
        </div>
      </el-card>

      <!--第四张卡片：详细数据表格 -->
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
                  <!-- 基准价信息 -->
                  <div class="benchmark-info" v-if="row.specification || row.brand || row.region || row.market">
                    <span class="benchmark-label">基准价</span>
                    <span v-if="row.specification">规格: {{ row.specification }}</span>
                    <span v-if="row.brand">品牌: {{ row.brand }}</span>
                    <span v-if="row.market">市场: {{ row.market }}</span>
                    <span>单价: ¥{{ row.price?.toLocaleString() }}/{{ row.unit || '吨' }}</span>
                  </div>
                  <!-- 品类历史基准价折线图 -->
                  <div class="expand-chart-section">
                    <div class="expand-chart-header">
                      <span class="expand-chart-title">历史基准价走势</span>
                      <el-select v-model="expandChartDays" size="small" style="width: 72px" @change="() => handleExpandChartDaysChange(row)">
                        <el-option label="7天" :value="7" />
                        <el-option label="30天" :value="30" />
                        <el-option label="90天" :value="90" />
                      </el-select>
                    </div>
                    <div :ref="el => expandChartRefs[row.product_id] = el" class="expand-chart-container" style="height: 200px; width: 100%;"></div>
                  </div>
                  <!-- 详细报价列表 -->
                  <p class="expand-title" v-if="row.extra_data?.详细报价?.length">
                    详细报价（{{ row.extra_data.详细报价.length }}家供应商）
                  </p>
                  <p class="expand-title" v-else-if="!row.extra_data?.详细报价?.length">暂无详细报价数据</p>
                  <template v-if="row.extra_data?.详细报价?.length">
                    <el-table :data="paginatedHistoryData" size="small" class="detail-table" style="table-layout: auto; width: 100%;">
                      <el-table-column prop="publish_date" label="日期" min-width="90" />
                      <el-table-column prop="spec_raw" label="规格" min-width="160" />
                      <el-table-column prop="brand" label="品牌/产地" min-width="100" />
                      <el-table-column prop="price" label="单价" min-width="100">
                        <template #default="{ row: detail }">
                          <span class="price-value">¥{{ Number(detail.price || 0).toLocaleString() }}</span>
                        </template>
                      </el-table-column>
                      <el-table-column prop="price_type" label="报价类型" min-width="90" />
                      <el-table-column prop="region" label="交货地" min-width="110" />
                      <el-table-column prop="supplier" label="交易商" min-width="150" show-overflow-tooltip>
                        <template #default="{ row: detail }">
                          <span>{{ detail.supplier || '-' }}</span>
                        </template>
                      </el-table-column>
                    </el-table>
                    <el-pagination
                      v-if="expandedRows.length > 0 && row.extra_data?.详细报价?.length > 0"
                      background
                      size="small"
                      layout="sizes, prev, pager, next"
                      :total="row.extra_data?.详细报价?.length || 0"
                      :page-size="historyPagination.pageSize"
                      :page-sizes="[10, 20, 50, 100]"
                      :current-page="historyPagination.page"
                      @size-change="handleHistorySizeChange"
                      @current-change="handleHistoryPageChange"
                      style="margin-top: 10px; justify-content: center"
                    />
                  </template>
                  <div v-else class="no-detail-data">
                    <span>暂无详细报价数据</span>
                  </div>
                </div>
              </template>
            </el-table-column>
            <template v-for="col in currentColumns" :key="col.prop">
              <el-table-column
                :prop="col.prop"
                :label="col.label"
                :min-width="col.minWidth"
                show-overflow-tooltip
              >
                <template #default="{ row }">
                  <span v-if="col.prop === 'price'" class="price-value">¥{{ row.price?.toLocaleString() }}</span>
                  <span v-else-if="col.prop === 'change_percent'" :class="row.change_percent > 0 ? 'text-rise' : row.change_percent < 0 ? 'text-fall' : 'text-flat'">
                    {{ row.change_percent > 0 ? '+' : '' }}{{ row.change_percent }}%
                  </span>
                  <span v-else-if="col.prop === 'trend'" :class="['trend-badge', row.trend]">
                    {{ row.trend === '涨' ? '↑' : row.trend === '跌' ? '↓' : '—' }}
                  </span>
                  <span v-else-if="col.useExtraData">{{ row.extra_data?.[col.useExtraData] || row[col.prop] || '-' }}</span>
                  <span v-else>{{ row[col.prop] || '-' }}</span>
                </template>
              </el-table-column>
            </template>
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
import { priceApi } from '../api/price.js'
import * as echarts from 'echarts'

import SourceSelector from '../components/SourceSelector.vue'
import IndustrySelector from '../components/IndustrySelector.vue'

const lineChartRef = ref(null)
const pieChartRef = ref(null)
const barChartRef = ref(null)
const expandChartRefs = ref({})

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


const filter1DateRange = ref([])
const filter1Source = ref(null)
const filter1Industry = ref(null)

watch(filter1Source, () => { loadFilter1Charts() })
watch(filter1Industry, () => { loadFilter1Charts() })


const filter2DateRange = ref([])
const filter2Source = ref(null)
const filter2Industry = ref(null)

watch(filter2Source, () => { loadFilter2Charts() })
watch(filter2Industry, () => { loadFilter2Charts() })


const filter3Source = ref(null)
const filter3Industry = ref(null)
const searchKeyword = ref('')



const pagination = ref({ page: 1, pageSize: 10, total: 0 })
const historyPagination = ref({ page: 1, pageSize: 10 })
const compareDays = ref(7)
const expandChartDays = ref(7)

// Supplier comparison card
const supplierChartRef = ref(null)
const supplierBarChartRef = ref(null)
const supplierProducts = ref([])
const selectedSupplierProduct = ref(null)
const supplierComparisonDays = ref(30)
let supplierPieChart = null
let supplierBarChart = null

const indicatorCards = ref([
  { metricType: 'yoy', metricLabel: '同比涨幅', productName: '-', changePercent: 0, trend: 'rise', price: 0, hasData: true },
  { metricType: 'qoq', metricLabel: '环比涨幅', productName: '-', changePercent: 0, trend: 'rise', price: 0, hasData: true },
  { metricType: 'd7', metricLabel: '7日涨跌', productName: '-', changePercent: 0, trend: 'rise', price: 0, hasData: true },
  { metricType: 'd30', metricLabel: '30日涨跌', productName: '-', changePercent: 0, trend: 'rise', price: 0, hasData: true }
])

// 行业列配置：各行业显示不同字段
// extra_data 字段说明:
//   化工: { '规格': '', '品牌/产地': brand, '报价类型': '市场价/基准价' }
//   能源: { '规格': spec, '数量': '', '现货类型': '', '有效时间': '' }
//   农副: { '分类': '', '等级/熔点': '', '品牌/产地': brand, '报价类型': '' }
//   有色: { '品名/纯度': name, '品牌/产地': region, '报价类型': '' }
const industryColumns = {
  '化工': [
    { prop: 'product_name', label: '商品名称', minWidth: 120 },
    { prop: 'specification', label: '规格', minWidth: 80 },
    { prop: 'brand', label: '品牌/产地', minWidth: 100 },
    { prop: 'price', label: '单价', minWidth: 100 },
    { prop: 'unit', label: '单位', minWidth: 70 },
    { prop: 'price_type', label: '报价类型', minWidth: 80 },
    { prop: 'region', label: '交货地', minWidth: 80 },
    { prop: 'supplier', label: '交易商', minWidth: 80 },
    { prop: 'change_percent', label: '较昨日涨跌幅', minWidth: 100 },
    { prop: 'trend', label: '趋势', minWidth: 60 },
    { prop: 'latest_date', label: '发布时间', minWidth: 100 },
    { prop: 'source', label: '数据源', minWidth: 80 }
  ],
  '能源': [
    { prop: 'product_name', label: '产品名', minWidth: 120 },
    { prop: 'specification', label: '规格', minWidth: 80 },
    { prop: 'price', label: '单价', minWidth: 100 },
    { prop: 'unit', label: '单位', minWidth: 70 },
    { prop: 'region', label: '交货地', minWidth: 80 },
    { prop: 'change_percent', label: '较昨日涨跌幅', minWidth: 100 },
    { prop: 'trend', label: '趋势', minWidth: 60 },
    { prop: 'latest_date', label: '发布时间', minWidth: 100 },
    { prop: 'source', label: '数据源', minWidth: 80 }
  ],
  '农副': [
    { prop: 'product_name', label: '商品名称', minWidth: 120 },
    { prop: 'specification', label: '规格', minWidth: 80 },
    { prop: 'brand', label: '产地', minWidth: 100 },
    { prop: 'price', label: '单价', minWidth: 100 },
    { prop: 'unit', label: '单位', minWidth: 70 },
    { prop: 'price_type', label: '报价类型', minWidth: 80 },
    { prop: 'region', label: '交货地', minWidth: 80 },
    { prop: 'supplier', label: '市场', minWidth: 80 },
    { prop: 'change_percent', label: '较昨日涨跌幅', minWidth: 100 },
    { prop: 'trend', label: '趋势', minWidth: 60 },
    { prop: 'latest_date', label: '发布时间', minWidth: 100 },
    { prop: 'source', label: '数据源', minWidth: 80 }
  ],
  '有色': [
    { prop: 'product_name', label: '商品名称', minWidth: 120, useExtraData: '品名/纯度' },
    { prop: 'specification', label: '规格', minWidth: 80 },
    { prop: 'brand', label: '产区', minWidth: 100 },
    { prop: 'price', label: '单价', minWidth: 100 },
    { prop: 'unit', label: '单位', minWidth: 70 },
    { prop: 'price_type', label: '报价类型', minWidth: 80 },
    { prop: 'region', label: '交货地', minWidth: 80 },
    { prop: 'supplier', label: '市场', minWidth: 80 },
    { prop: 'change_percent', label: '较昨日涨跌幅', minWidth: 100 },
    { prop: 'trend', label: '趋势', minWidth: 60 },
    { prop: 'latest_date', label: '发布时间', minWidth: 100 },
    { prop: 'source', label: '数据源', minWidth: 80 }
  ]
}

// 默认列（未选择行业时）
const defaultColumns = [
  { prop: 'product_name', label: '产品名称', minWidth: 150 },
  { prop: 'price', label: '最新价格', minWidth: 110 },
  { prop: 'change_percent', label: '较昨日涨跌幅', minWidth: 110 },
  { prop: 'trend', label: '趋势', minWidth: 80 },
  { prop: 'latest_date', label: '最新日期', minWidth: 110 },
  { prop: 'source', label: '数据源', minWidth: 100 }
]

const currentColumns = computed(() => {
  const industry = filter3Industry.value
  if (industry && industryColumns[industry]) {
    return industryColumns[industry]
  }
  return defaultColumns
})

let lineChart = null
let pieChart = null
let barChart = null
let searchTimer = null

const pieColors = ['#0077cc', '#00a8e8', '#4db8e8', '#005fa3', '#003d6b', '#006594', '#0077cc', '#00a8e8', '#e91e63', '#6739b6']

async function loadLatestPrices() {
  try {
    const params = {
      category_id: null,
      subcategory_id: null,
      source: filter3Source.value || null,
      industry: filter3Industry.value || null
    }
    const res = await priceApi.getLatestPrices(params)
    latestPrices.value = res.data.data || []
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
  if (!row || !row.extra_data?.详细报价 || row.extra_data.详细报价.length === 0) return []
  const start = (historyPagination.value.page - 1) * historyPagination.value.pageSize
  const end = start + historyPagination.value.pageSize
  return row.extra_data.详细报价.slice(start, end)
})

watch(paginatedHistoryData, () => { nextTick(() => {}) }, { deep: true })

async function handleExpandChange(row) {
  const id = row.product_id
  if (expandedRows.value.includes(id)) {
    expandedRows.value = []
  } else {
    expandedRows.value = [id]
    historyPagination.value.page = 1
    await nextTick()
    loadExpandChart(row)
  }
}

async function loadExpandChart(row) {
  const el = expandChartRefs.value[row.product_id]
  if (!el) return
  const chart = echarts.init(el)
  try {
    // 使用基准价历史数据（与表格数据源一致）
    const res = await priceApi.getBenchmarkHistory(
      row.product_id,
      expandChartDays.value,
      null
    )
    if (!res.data || res.data.length === 0) {
      chart.setOption({ series: [] })
      return
    }
    const data = res.data
    const dates = data.map(d => d.record_date)
    const prices = data.map(d => d.price)
    const productName = data[0]?.product_name || row.product_name || '基准价'
    // 计算Y轴范围（自适应数据）
    const axisRange = getNiceAxisRange(prices)
    chart.setOption({
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#fff',
        borderColor: '#E8E3F3',
        borderWidth: 1,
        textStyle: { color: '#1E293B', fontSize: 12 },
        borderRadius: 8,
        formatter: (params) => {
          const date = params[0].axisValue
          let html = `<strong>${date}</strong><br/>`
          params.forEach(p => {
            html += `<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${p.color};margin-right:6px;"></span>${p.seriesName}: <strong>¥${p.value?.toLocaleString() ?? '-'}</strong><br/>`
          })
          return html
        }
      },
      grid: { left: 50, right: 20, bottom: 30, top: 10, containLabel: true },
      xAxis: {
        type: 'category',
        data: dates,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#94A3B4', fontSize: 10 }
      },
      yAxis: {
        type: 'value',
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#94A3B4', fontSize: 10, formatter: val => `¥${val.toLocaleString()}` },
        splitLine: { lineStyle: { color: '#E8E3F3', type: 'dashed' } },
        ...(axisRange ? { min: axisRange.min, max: axisRange.max } : {}),
        scale: true
      },
      series: [{
        name: productName,
        type: 'line',
        data: prices,
        smooth: true,
        symbol: 'circle',
        symbolSize: 3,
        lineStyle: { width: 2, color: '#E63946' },
        itemStyle: { color: '#E63946' },
        emphasis: { itemStyle: { borderColor: '#fff', borderWidth: 2 } },
        connectNulls: true
      }]
    })
  } catch (e) {
    console.error('Failed to load expand chart', e)
  }
}

function handleExpandChartDaysChange(row) {
  loadExpandChart(row)
}

function handleHistoryPageChange(page) {
  historyPagination.value.page = page
}

function handleHistorySizeChange(size) {
  historyPagination.value.pageSize = size
  historyPagination.value.page = 1
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
    loadIndicatorCards(),
    loadSupplierComparison()
  ])
}

async function loadIndicatorCards() {
  try {
    const params = {
      source: filter2Source.value || null,
      category_id: null,
      subcategory_id: null,
      industry: filter2Industry.value || null
    }

    // 并行加载所有4种指标
    const [yoyRes, qoqRes, d7Res, d30Res] = await Promise.all([
      priceApi.getDashboardIndicatorCards({ ...params, period_type: 'yoy' }),
      priceApi.getDashboardIndicatorCards({ ...params, period_type: 'qoq' }),
      priceApi.getDashboardIndicatorCards({ ...params, period_type: 'd7' }),
      priceApi.getDashboardIndicatorCards({ ...params, period_type: 'd30' })
    ])

    const metricMap = {
      yoy: yoyRes.data.items || [],
      qoq: qoqRes.data.items || [],
      d7: d7Res.data.items || [],
      d30: d30Res.data.items || []
    }

    // 更新每个卡片
    for (let i = 0; i < indicatorCards.value.length; i++) {
      const card = indicatorCards.value[i]
      const items = metricMap[card.metricType] || []
      if (items.length > 0) {
        const top1 = items[0]
        indicatorCards.value[i] = {
          ...card,
          productName: top1.product_name,
          changePercent: Math.abs(top1.change_percent),
          trend: top1.change_percent >= 0 ? 'rise' : 'fall',
          price: top1.latest_price || 0,
          hasData: true
        }
      } else {
        // 无数据时显示提示
        const noDataMsg = {
          yoy: '暂无去年同比数据',
          qoq: '暂无上月环比数据',
          d7: '暂无7日数据',
          d30: '暂无30日数据'
        }
        indicatorCards.value[i] = {
          ...card,
          productName: noDataMsg[card.metricType] || '暂无数据',
          changePercent: 0,
          trend: 'rise',
          price: 0,
          hasData: false
        }
      }
    }
  } catch (e) {
    console.error('Failed to load indicator cards', e)
  }
}

async function onMetricTypeChange(idx) {
  // 当用户切换指标类型时，重新加载该卡片数据
  try {
    const card = indicatorCards.value[idx]
    const params = {
      period_type: card.metricType,
      source: filter2Source.value || null,
      category_id: null,
      subcategory_id: null,
      industry: filter2Industry.value || null
    }
    const res = await priceApi.getDashboardIndicatorCards(params)
    const items = res.data.items || []
    if (items.length > 0) {
      const top1 = items[0]
      indicatorCards.value[idx] = {
        ...card,
        metricLabel: getMetricLabel(card.metricType),
        productName: top1.product_name,
        changePercent: Math.abs(top1.change_percent),
        trend: top1.change_percent >= 0 ? 'rise' : 'fall',
        price: top1.latest_price || 0,
        hasData: true
      }
    } else {
      const noDataMsg = { yoy: '暂无去年同比数据', qoq: '暂无上月环比数据', d7: '暂无7日数据', d30: '暂无30日数据' }
      indicatorCards.value[idx] = {
        ...card,
        metricLabel: getMetricLabel(card.metricType),
        productName: noDataMsg[card.metricType] || '暂无数据',
        changePercent: 0,
        trend: 'rise',
        price: 0,
        hasData: false
      }
    }
  } catch (e) {
    console.error('Failed to load indicator card', e)
  }
}

function getMetricLabel(metricType) {
  const labels = { yoy: '同比涨幅', qoq: '环比涨幅', d7: '7日涨跌', d30: '30日涨跌' }
  return labels[metricType] || metricType
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

    // 使用基准价历史数据（与表格数据源一致）
    const res = await priceApi.getBenchmarkHistoryMulti({
      days,
      
      source: filter1Source.value || null,
      industry: filter1Industry.value || null
    })

    if (!res.data || !res.data.dates || res.data.dates.length === 0) {
      lineChart.setOption({ series: [] })
      lineChartRawData.value = { dates: [], series: [] }
      return
    }

    const { dates, series } = res.data
    lineChartRawData.value = { dates, series }
    const lineColors = ['#E63946', '#2A9D5C', '#E9C46A', '#264653', '#F4A261', '#8E44AD', '#1ABC9C', '#E74C3C', '#3498DB', '#9B59B6']

    // 计算Y轴范围（自适应数据）
    const allPrices = series.flatMap(s => s.data.filter(v => v != null))
    const axisRange = getNiceAxisRange(allPrices)

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
        splitLine: { lineStyle: { color: '#F0EBF9', type: 'dashed' } },
        ...(axisRange ? { min: axisRange.min, max: axisRange.max } : {}),
        scale: true
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
  console.log('[Ranking] loadRankingData called, barChart:', !!barChart)
  if (!barChart) {
    console.log('[Ranking] barChart not initialized, skipping')
    return
  }
  try {
    console.log('[Ranking] Fetching ranking data...')
    let days = compareDays.value
    if (filter1DateRange.value && filter1DateRange.value.length === 2) {
      const start = new Date(filter1DateRange.value[0])
      const end = new Date(filter1DateRange.value[1])
      days = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1
    }

    const params = {
      limit: 10,
      days: days,
      
      source: filter1Source.value || null,
      industry: filter1Industry.value || null
    }
    console.log('[Ranking] Params:', params)
    const res = await priceApi.getDashboardRanking(params)
    console.log('[Ranking] Response data:', JSON.stringify(res.data))
    const rising = res.data.rising || []
    const falling = res.data.falling || []
    console.log('[Ranking] Rising:', rising.map(x => `${x.product_name}:${x.change_percent}`))
    console.log('[Ranking] Falling:', falling.map(x => `${x.product_name}:${x.change_percent}`))
    console.log('[Ranking] Rising:', rising.length, 'Falling:', falling.length)
    rankingData.value = { rising, falling }
    // 合并涨跌数据：涨幅取前5，跌幅取前5，0%产品保留在对应位置（后端已返回全部产品）
    const topRising = rising.slice(0, 5)
    const topFalling = falling.slice(0, 5)
    // 去重（0%产品可能在两个列表中都出现）
    const seen = new Set()
    const combined = [...topRising, ...topFalling].filter(x => {
      if (seen.has(x.product_id)) return false
      seen.add(x.product_id)
      return true
    })
    const categories = combined.map(r => r.product_name.substring(0, 8))
    const values = combined.map(r => r.change_percent)
    barChartRawData.value = {
      categories,
      values,
      fullData: combined
    }
    if (combined.length > 0) {
      barChart.setOption({
        yAxis: { data: categories },
        series: [{ data: values }]
      })
    }
  } catch (e) {
    console.error('[Ranking] Failed to load ranking data', e)
  }
}

async function loadDistributionData() {
  if (!pieChart) return
  try {
    const params = {
      days: 30,
      source: filter2Source.value || null,
      category_id: null,
      subcategory_id: null,
      industry: filter2Industry.value || null
    }
    const res = await priceApi.getDashboardDistribution(params)
    if (res.data.labels && res.data.labels.length > 0) {
      pieChartRawData.value = {
        labels: res.data.labels,
        sizes: res.data.sizes
      }
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

async function loadSupplierComparison() {
  try {
    const params = {
      days: supplierComparisonDays.value,
      source: filter2Source.value || null,
      industry: filter2Industry.value || null
    }
    if (selectedSupplierProduct.value) {
      params.product_id = selectedSupplierProduct.value
    }
       const res = await priceApi.getSupplierComparison(params)
    const data = res.data || {}

    // Update pie chart: supplier quote counts
    if (supplierPieChart && data.supplier_counts?.length > 0) {
      supplierPieChart.setOption({
        series: [{
          data: data.supplier_counts.map((s, i) => ({
            name: s.supplier,
            value: s.count,
            itemStyle: { color: pieColors[i % pieColors.length] }
          }))
        }]
      })
    }

    // Update bar chart: same product multi-supplier price comparison
    if (supplierBarChart && data.product_supplier_prices?.length > 0) {
      const sorted = [...data.product_supplier_prices].sort((a, b) => b.price - a.price)
      const categories = sorted.map(s => s.supplier.substring(0, 10))
      const values = sorted.map(s => s.price)
      const barColors = values.map(v => {
        const min = Math.min(...values)
        const max = Math.max(...values)
        const ratio = max > min ? (v - min) / (max - min) : 0
        return ratio > 0.6 ? '#E63946' : ratio > 0.3 ? '#E9C46A' : '#2A9D5C'
      })
      supplierBarChart.setOption({
        yAxis: { data: categories },
        series: [{
          data: values.map((v, i) => ({ value: v, itemStyle: { color: barColors[i] } }))
        }]
      })
    }

    supplierProducts.value = data.supplier_products || []
  } catch (e) {
    console.error('Failed to load supplier comparison', e)
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

function getNiceAxisRange(prices) {
  if (!prices || prices.length === 0) return null
  const min = Math.min(...prices)
  const max = Math.max(...prices)
  if (min === max) {
    // 单点数据，往上下各扩展10%
    const padding = min * 0.1 || 100
    return { min: min - padding, max: max + padding }
  }
  // 计算合适的刻度间隔
  const range = max - min
  // 根据数据大小选择合适的"根"值
  const magnitude = Math.pow(10, Math.floor(Math.log10(range)))
  const normalized = range / magnitude
  // 选择合适的步长（1, 2, 5, 10的倍数）
  let step
  if (normalized <= 1) step = magnitude / 10
  else if (normalized <= 2) step = magnitude / 5
  else if (normalized <= 5) step = magnitude / 2
  else step = magnitude
  // 计算nice的min和max（向下取整到step的整数倍，向上取整到step的整数倍）
  const niceMin = Math.floor(min / step) * step
  const niceMax = Math.ceil(max / step) * step
  return { min: niceMin, max: niceMax }
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
    yAxis: { type: 'value', axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#94A3B4', fontSize: 11, formatter: val => `¥${val.toLocaleString()}` }, splitLine: { lineStyle: { color: '#F0EBF9', type: 'dashed' } }, scale: true },
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
      itemStyle: { color: (params) => params.value > 0 ? '#E63946' : params.value < 0 ? '#2A9D5C' : '#909399', borderRadius: [0, 4, 4, 0] },
      barWidth: '60%'
    }]
  })
}

function initSupplierCharts() {
  if (supplierChartRef.value) {
    if (supplierPieChart) supplierPieChart.dispose()
    supplierPieChart = echarts.init(supplierChartRef.value)
    supplierPieChart.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'item', formatter: '{b}: {c}条报价 ({d}%)', backgroundColor: '#fff', borderColor: '#E8E3F3', textStyle: { color: '#1E293B' }, borderRadius: 8 },
      legend: { orient: 'vertical', left: 'left', top: 'center', textStyle: { color: '#64748B', fontSize: 10 }, itemGap: 6, width: 70 },
      series: [{ type: 'pie', radius: ['28%', '60%'], center: ['55%', '50%'], label: { show: false }, emphasis: { label: { show: false } } }]
    })
  }

  if (supplierBarChartRef.value) {
    if (supplierBarChart) supplierBarChart.dispose()
    supplierBarChart = echarts.init(supplierBarChartRef.value)
    supplierBarChart.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: '#E8E3F3', textStyle: { color: '#1E293B' }, axisPointer: { type: 'shadow' }, borderRadius: 8, formatter: (params) => `<strong>${params[0].name}</strong><br/>价格: ¥${params[0].value?.toLocaleString() ?? '-'}` },
      grid: { left: '3%', right: '8%', bottom: '3%', top: '3%', containLabel: true },
      xAxis: { type: 'value', axisLine: { show: false }, axisLabel: { color: '#94A3B4' }, splitLine: { lineStyle: { color: '#F0EBF9', type: 'dashed' } } },
      yAxis: { type: 'category', data: [], axisLine: { lineStyle: { color: '#E8E3F3' } }, axisLabel: { color: '#64748B', fontSize: 10 } },
      series: [{ type: 'bar', barWidth: '60%' }]
    })
  }
}

onMounted(async () => {
  initLineChart()
  initPieChart()
  initBarChart()
  initSupplierCharts()
  setTimeout(() => {
    lineChart?.resize()
    pieChart?.resize()
    barChart?.resize()
    supplierPieChart?.resize()
    supplierBarChart?.resize()
  }, 100)
  await nextTick()
  await nextTick()
  await nextTick()
  setTimeout(() => {
    loadLatestPrices()
    loadFilter1Charts()
    loadFilter2Charts()
  }, 200)
  window.addEventListener('resize', () => {
    lineChart?.resize()
    pieChart?.resize()
    barChart?.resize()
    supplierPieChart?.resize()
    supplierBarChart?.resize()
  })
})

onUnmounted(() => {
  lineChart?.dispose()
  pieChart?.dispose()
  barChart?.dispose()
  supplierPieChart?.dispose()
  supplierBarChart?.dispose()
  Object.values(expandChartRefs.value).forEach(el => {
    if (el) {
      const chart = echarts.getInstanceByDom(el)
      chart?.dispose()
    }
  })
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
  gap: 16px;
  align-items: stretch;
}

.chart-4 {
  flex: 0 0 50%;
  display: flex;
  align-items: stretch;
  min-height: 200px;
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
  min-height: 200px;
}

.chart-title {
  display: none;
}

.indicator-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  flex: 1;
  overflow: hidden;
  padding-right: 8px;
}

.indicator-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  opacity: 0;
  animation: fadeInUp 0.4s ease-out forwards;
}

.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.card-placeholder {
  flex: 1;
}

.card-label {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 500;
}

.card-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 100%;
}

.card-body.no-data .card-product {
  color: var(--text-muted);
  font-size: 12px;
}

.card-body.no-data .value-num {
  color: var(--text-muted);
  font-size: 16px;
}

.card-body.no-data .card-price {
  visibility: hidden;
}

.card-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.card-product {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 600;
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-value {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
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
  font-size: 24px;
  font-weight: 700;
  font-family: 'Fira Sans', sans-serif;
}

.card-value.rise .value-num {
  color: var(--rise-color);
}

.card-value.fall .value-num {
  color: var(--fall-color);
}

.card-price {
  font-size: 12px;
  color: var(--text-muted);
  text-align: right;
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
  margin-top: 0;
  border-top: none;
  padding-top: 0;
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

.expand-content .el-table__body-wrapper {
  overflow: visible !important;
  width: 100% !important;
}

.expand-content .el-table__body-wrapper table {
  table-layout: auto !important;
  width: 100% !important;
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
  overflow: visible;
  min-width: 0;
}

.history-sparkline {
  display: none;
}

.no-detail-data {
  text-align: center;
  color: var(--text-muted);
  padding: 24px;
  font-size: 13px;
}

.expand-title {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 12px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.benchmark-info {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 6px;
  margin-bottom: 12px;
  font-size: 13px;
  color: #606266;
}
.benchmark-info .benchmark-label {
  font-weight: 600;
  color: #303133;
}

.expand-chart-section {
  margin-bottom: 12px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 6px;
}

.expand-chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.expand-chart-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.expand-chart-container {
  min-height: 200px;
}

.detail-table {
  background: transparent !important;
  width: 100% !important;
  table-layout: auto !important;
}
.detail-table .el-table__header,
.detail-table .el-table__body,
.detail-table .el-table__footer {
  table-layout: auto !important;
  width: 100% !important;
}
.detail-table .el-table__body-wrapper {
  width: 100% !important;
  overflow: visible !important;
}
.detail-table .el-table__body-wrapper table {
  width: 100% !important;
  table-layout: auto !important;
}
.detail-table .el-table__header-wrapper {
  width: 100% !important;
}
.detail-table .el-table__header-wrapper table {
  width: 100% !important;
  table-layout: auto !important;
}
.detail-table td.el-table__cell,
.detail-table th.el-table__cell {
  width: auto !important;
}
.detail-table .el-table__body {
  width: 100% !important;
}
.detail-table .el-table__header {
  width: 100% !important;
}
.detail-table.is-scrolling-none {
  width: 100% !important;
}
.detail-table.el-table--layout-fixed {
  table-layout: auto !important;
  width: 100% !important;
}
.detail-table .el-table__header,
.detail-table .el-table__body,
.detail-table .el-table__footer {
  table-layout: auto !important;
  width: 100% !important;
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
  .charts-grid-46 { flex-direction: column; }
  .chart-4 { flex: none; width: 100%; }
}

@media (max-width: 768px) {
  .controls { flex-direction: column; align-items: stretch; }
  .dashboard { padding: 16px; }
}

.data-table {
  width: 100% !important;
}

.table-section :deep(.el-table) {
  width: 100% !important;
}

.table-section :deep(.el-table__body-wrapper) {
  overflow: hidden !important;
}

.table-section :deep(.el-table__header-wrapper) {
  overflow: hidden !important;
}

.table-section :deep(.el-table__expanded-cell) {
  overflow: visible !important;
}

.table-section :deep(.el-table__expanded-cell .el-table__body-wrapper) {
  overflow: visible !important;
}

.table-section :deep(.el-table__expanded-cell .el-table__body-wrapper table) {
  width: 100% !important;
  table-layout: auto !important;
}

.supplier-table {
  margin-top: 8px;
}
</style>