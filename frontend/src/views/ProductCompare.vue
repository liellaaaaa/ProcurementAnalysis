<template>
  <div class="compare-page">
    <header class="header">
      <h1>产品对比</h1>
      <nav>
        <router-link to="/">价格看板</router-link>
        <router-link to="/compare">产品对比</router-link>
      </nav>
    </header>

    <div class="content">
      <el-card class="selector-card">
        <template #header>
          <div class="card-header">
            <span>选择产品进行对比</span>
            <SourceSelector @update:source="val => { selectedSource = val; loadComparison() }" />
          </div>
        </template>
        <el-select
          v-model="selectedProducts"
          multiple
          placeholder="选择产品"
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
      </el-card>

      <el-card class="chart-card">
        <template #header>
          <span>价格对比趋势</span>
        </template>
        <div ref="chartRef" class="chart-container"></div>
      </el-card>
    </div>
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

    updateChart(allData.map(res => ({
      name: products.value.find(p => p.id === res.config.params.productId)?.product_name || '',
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

  const colors = ['#409eff', '#67c23a', '#f56c6c', '#e6a23c', '#909399']
  const allDates = [...new Set(seriesData.flatMap(s => s.data.map(d => d.record_date)))].sort()

  const series = seriesData.map((s, i) => ({
    name: s.name,
    type: 'line',
    smooth: true,
    data: allDates.map(date => {
      const record = s.data.find(d => d.record_date === date)
      return record ? record.price : null
    }),
    connectNulls: true,
    itemStyle: { color: colors[i % colors.length] }
  }))

  const option = {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: series.map(s => s.name)
    },
    xAxis: {
      type: 'category',
      data: allDates
    },
    yAxis: {
      type: 'value',
      name: '价格'
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

.selector-card {
  margin-bottom: 20px;
}

.chart-card {
  margin-bottom: 20px;
}

.chart-container {
  height: 400px;
}
</style>