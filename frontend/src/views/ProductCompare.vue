<template>
  <div class="compare-page">
    <div class="page-container">
      <header class="page-header">
      </header>

      <el-card class="selector-card animate-in">
        <template #header>
          <div class="card-header">
            <div class="header-title">
              <div class="title-icon-wrapper">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="2" y1="12" x2="22" y2="12"/>
                  <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
                </svg>
              </div>
              <span>选择产品进行对比</span>
            </div>
          </div>
        </template>

        <div class="selector-row">
          <SourceSelector @update:source="val => { selectedSource = val; loadComparison() }" />
          <IndustrySelector v-model="selectedIndustry" />
        </div>

        <el-select
          v-model="selectedProducts"
          multiple
          placeholder="选择至少2个产品进行对比"
          style="width: 100%; margin-top: 12px"
          @change="loadComparison"
          class="product-select"
        >
          <el-option
            v-for="p in filteredProducts"
            :key="p.id"
            :label="p.product_name"
            :value="p.id"
          >
            <span class="product-option">
              <span class="product-dot"></span>
              {{ p.product_name }}
            </span>
          </el-option>
        </el-select>

        <div class="date-row">
          <span class="date-label">时间范围</span>
          <PeriodSelector v-model:startDate="compareStart" v-model:endDate="compareEnd" />
        </div>

        <div v-if="selectedProducts.length < 2" class="hint-box">
          <div class="hint-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="16" x2="12" y2="12"/>
              <line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
          </div>
          <span>请选择至少2个产品以查看对比图表</span>
        </div>
      </el-card>

      <el-card class="chart-card animate-in" style="animation-delay: 0.1s" v-show="selectedProducts.length >= 2">
        <template #header>
          <div class="card-header">
            <div class="header-title">
              <div class="title-icon-wrapper">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
                  <polyline points="17 6 23 6 23 12"/>
                </svg>
              </div>
              <span>价格对比趋势</span>
            </div>
            <div class="product-tags">
              <span v-for="id in selectedProducts.slice(0, 5)" :key="id" class="product-tag">
                <span class="tag-dot" :style="{background: getProductColor(id)}"></span>
                {{ products.find(p => p.id === id)?.product_name }}
              </span>
            </div>
          </div>
        </template>
        <div ref="chartRef" class="chart-container"></div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, computed } from 'vue'
import { priceApi } from '../api/price.js'
import { productApi } from '../api/product.js'
import SourceSelector from '../components/SourceSelector.vue'
import IndustrySelector from '../components/IndustrySelector.vue'
import PeriodSelector from '../components/PeriodSelector.vue'
import * as echarts from 'echarts'

const chartRef = ref(null)
const products = ref([])
const selectedProducts = ref([])
const selectedSource = ref(null)
const selectedIndustry = ref(null)
const compareStart = ref(null)
const compareEnd = ref(null)
let chartInstance = null

const colors = ['#0077cc', '#00a8e8', '#4db8e8', '#005fa3', '#003d6b', '#006594']

const filteredProducts = computed(() => {
  return products.value
})

// 监听行业变化，重新加载产品列表
watch(selectedIndustry, (newIndustry) => {
  selectedProducts.value = []
  loadProducts()
})

watch([compareStart, compareEnd], () => { loadComparison() })

function getProductColor(id) {
  const idx = selectedProducts.value.indexOf(id)
  return colors[idx % colors.length]
}

async function loadProducts() {
  try {
    const params = { limit: 500 }
    if (selectedIndustry.value) {
      params.industry = selectedIndustry.value
    }
    console.log('loadProducts params:', params)
    const res = await productApi.getProducts(params)
    console.log('loadProducts result count:', res.data?.length)
    products.value = res.data || []
  } catch (e) {
    console.error('Failed to load products', e)
  }
}

function getNiceAxisRange(prices) {
  if (!prices || prices.length === 0) return null
  const min = Math.min(...prices)
  const max = Math.max(...prices)
  if (min === max) {
    const padding = min * 0.1 || 100
    return { min: min - padding, max: max + padding }
  }
  const range = max - min
  const magnitude = Math.pow(10, Math.floor(Math.log10(range)))
  const normalized = range / magnitude
  let step
  if (normalized <= 1) step = magnitude / 10
  else if (normalized <= 2) step = magnitude / 5
  else if (normalized <= 5) step = magnitude / 2
  else step = magnitude
  const niceMin = Math.floor(min / step) * step
  const niceMax = Math.ceil(max / step) * step
  return { min: niceMin, max: niceMax }
}

async function loadComparison() {
  if (selectedProducts.value.length < 2) return

  try {
    let days = 30
    if (compareStart.value && compareEnd.value) {
      const start = new Date(compareStart.value + 'T00:00:00')
      const end = new Date(compareEnd.value + 'T00:00:00')
      days = Math.max(1, Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1)
    } else if (!compareStart.value && !compareEnd.value) {
      days = 365
    }

    const allData = await Promise.all(
      selectedProducts.value.map(id => priceApi.getBenchmarkHistory(id, days, selectedSource.value))
    )

    updateChart(allData.map((res, i) => ({
      name: res.data[0]?.product_name || products.value.find(p => p.id === selectedProducts.value[i])?.product_name || '',
      data: res.data
    })))
  } catch (e) {
    console.error('Failed to load comparison', e)
  }
}

function updateChart(seriesData) {
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  const allDates = [...new Set(seriesData.flatMap(s => s.data.map(d => d.record_date)))].sort()

  const series = seriesData.map((s, i) => ({
    name: s.name,
    type: 'line',
    smooth: true,
    symbol: 'circle',
    symbolSize: 6,
    data: allDates.map(date => {
      const record = s.data.find(d => d.record_date === date)
      return record ? record.price : null
    }),
    connectNulls: true,
    itemStyle: { color: colors[i % colors.length] },
    lineStyle: { width: 2.5 }
  }))

  const allPrices = seriesData.flatMap(s => s.data.map(d => d.price)).filter(v => v != null)
  const axisRange = getNiceAxisRange(allPrices)

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#fff',
      borderColor: '#E8E3F3',
      borderWidth: 1,
      borderRadius: 8,
      textStyle: { color: '#1E293B' },
      boxShadow: '0 2px 8px rgba(139, 92, 246, 0.08)'
    },
    legend: {
      data: series.map(s => s.name),
      bottom: 0,
      textStyle: { color: '#64748B', fontSize: 11 },
      itemWidth: 20,
      itemHeight: 10
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '5%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: allDates,
      boundaryGap: false,
      axisLine: { lineStyle: { color: '#E8E3F3' } },
      axisLabel: { color: '#94A3B8', fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      name: '价格 (元/吨)',
      nameTextStyle: { color: '#64748B', fontSize: 11 },
      axisLine: { show: false },
      axisLabel: { color: '#94A3B8', fontSize: 11 },
      splitLine: { lineStyle: { color: '#F0EBF9', type: 'dashed' } },
      ...(axisRange ? { min: axisRange.min, max: axisRange.max } : {}),
      scale: true
    },
    series
  }

  chartInstance.setOption(option, { notMerge: true })
}

onMounted(() => {
  loadProducts()
  window.addEventListener('resize', () => chartInstance?.resize())
})

onUnmounted(() => {
  chartInstance?.dispose()
})
</script>

<style scoped>
.compare-page {
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

.selector-card {
  margin-bottom: 20px;
  border-radius: 16px !important;
}

.chart-card {
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

.selector-row {
  display: flex;
  gap: 12px;
  align-items: center;
}

.product-select :deep(.el-select__tags) {
  flex-wrap: wrap;
  gap: 4px;
}

.product-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.product-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-primary);
}

.date-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
  padding: 10px 12px;
  background: var(--bg-primary);
  border-radius: 8px;
}

.date-label {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

.date-buttons {
  display: flex;
  gap: 6px;
}

.hint-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: var(--bg-primary);
  border-radius: 8px;
  margin-top: 16px;
  color: var(--text-muted);
  font-size: 13px;
}

.hint-icon {
  color: var(--color-primary-light);
}

.product-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.product-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  padding: 4px 12px;
  background: var(--bg-primary);
  color: var(--text-secondary);
  border-radius: 16px;
  font-weight: 500;
}

.tag-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.chart-container {
  height: 400px;
  margin-top: 16px;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

.animate-in {
  opacity: 0;
  animation: fadeInUp 0.5s ease-out forwards;
}
</style>