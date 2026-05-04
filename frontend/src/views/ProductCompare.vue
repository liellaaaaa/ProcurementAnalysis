<template>
  <div class="compare-page">
    <header class="page-header">
      <div class="header-left">
        <h1 class="page-title">产品对比</h1>
        <p class="page-subtitle">多维度分析市场竞争态势</p>
      </div>
    </header>

    <el-card class="selector-card animate-in">
      <template #header>
        <div class="card-header">
          <div class="header-title">
            <span class="title-icon">⬡</span>
            <span>选择产品进行对比</span>
          </div>
          <SourceSelector @update:source="val => { selectedSource = val; loadComparison() }" />
        </div>
      </template>
      <el-select
        v-model="selectedProducts"
        multiple
        placeholder="选择至少2个产品进行对比"
        style="width: 100%"
        @change="loadComparison"
      >
        <el-option
          v-for="p in products"
          :key="p.id"
          :label="p.product_name"
          :value="p.id"
        />
      </el-select>
      <div v-if="selectedProducts.length < 2" class="hint-text">
        请选择至少2个产品以查看对比图表
      </div>
    </el-card>

    <el-card class="chart-card animate-in" style="animation-delay: 0.2s">
      <template #header>
        <div class="card-header">
          <div class="header-title">
            <span class="title-icon">◎</span>
            <span>价格对比趋势</span>
          </div>
          <div class="product-tags">
            <span v-for="id in selectedProducts.slice(0, 5)" :key="id" class="product-tag">
              {{ products.find(p => p.id === id)?.product_name }}
            </span>
          </div>
        </div>
      </template>
      <div ref="chartRef" class="chart-container"></div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { priceApi, productApi } from '../api/price'
import SourceSelector from '../components/SourceSelector.vue'
import * as echarts from 'echarts'

const chartRef = ref(null)
const products = ref([])
const selectedProducts = ref([])
const selectedSource = ref(null)
let chartInstance = null

const colors = ['#00d4ff', '#ff6b6b', '#00c48c', '#ffd93d', '#9b59b6', '#3498db']

async function loadProducts() {
  try {
    const res = await productApi.getProducts({ limit: 100 })
    products.value = res.data
  } catch (e) {
    console.error('Failed to load products', e)
  }
}

async function loadComparison() {
  if (selectedProducts.value.length < 2) return

  try {
    const allData = await Promise.all(
      selectedProducts.value.map(id => priceApi.getPriceHistory(id, 30, selectedSource.value))
    )

    updateChart(allData.map((res, i) => ({
      name: products.value.find(p => p.id === selectedProducts.value[i])?.product_name || '',
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
    lineStyle: { width: 2 }
  }))

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#21262d',
      borderColor: '#30363d',
      textStyle: { color: '#e8eaed' }
    },
    legend: {
      data: series.map(s => s.name),
      bottom: 0,
      textStyle: { color: '#8b949e' },
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
    series
  }

  chartInstance.setOption(option)
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

.product-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.product-tag {
  font-size: 12px;
  padding: 4px 10px;
  background: var(--accent-cyan-dim);
  color: var(--accent-cyan);
  border-radius: 12px;
}

.hint-text {
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
  margin-top: 16px;
}

.chart-container {
  height: 400px;
  margin-top: 16px;
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