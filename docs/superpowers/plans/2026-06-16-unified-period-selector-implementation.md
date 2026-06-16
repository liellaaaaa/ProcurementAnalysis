# PeriodSelector 统一时间筛选组件实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建统一的时间筛选组件 `<PeriodSelector>`，替换 Dashboard、ProductCompare、ReportView 中各自为政的时间筛选逻辑。

**Architecture:** 组件封装快捷按钮（1d/7d/30d/90d/all）+ 自定义 picker，emit `start_date/end_date`（`YYYY-MM-DD`）。父组件监听变化各自发起 API 请求，各卡片时间范围彼此独立。

**Tech Stack:** Vue3 Composition API + Element Plus el-date-picker + el-button

---

## 文件结构

```
frontend/src/components/PeriodSelector.vue      ← 新建：统一时间筛选组件
frontend/src/views/Dashboard.vue                ← 修改：接入3个卡片，删除废弃变量
frontend/src/views/ProductCompare.vue           ← 修改：替换旧时间筛选
frontend/src/views/ReportView.vue               ← 修改：周报模式接入 PeriodSelector
```

---

## Task 1: 创建 PeriodSelector.vue 组件

**Files:**
- Create: `frontend/src/components/PeriodSelector.vue`

### Step 1: 创建组件基础结构

```vue
<template>
  <div class="period-selector">
    <!-- 快捷按钮行 -->
    <div class="period-buttons" v-show="period !== 'custom'">
      <el-button
        v-for="p in periodOptions"
        :key="p.value"
        :type="period === p.value ? 'primary' : 'default'"
        size="small"
        @click="selectPeriod(p.value)"
      >{{ p.label }}</el-button>
      <el-button size="small" @click="showCustom">自定义</el-button>
    </div>
    <!-- 自定义 picker（默认隐藏） -->
    <div class="period-custom" v-show="period === 'custom'">
      <el-date-picker
        v-model="customRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始"
        end-placeholder="结束"
        value-format="YYYY-MM-DD"
        size="small"
        style="width: 220px"
        @change="onCustomChange"
      />
      <el-button size="small" @click="hideCustom">取消</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  startDate: { type: String, default: null },
  endDate: { type: String, default: null }
})
const emit = defineEmits(['update:startDate', 'update:endDate'])

// period: '1d' | '7d' | '30d' | '90d' | 'all' | 'custom'
const period = ref('7d')
const customRange = ref(null)

const periodOptions = [
  { label: '1天', value: '1d' },
  { label: '7天', value: '7d' },
  { label: '30天', value: '30d' },
  { label: '90天', value: '90d' },
  { label: '全部', value: 'all' }
]

function today() {
  return new Date().toISOString().split('T')[0]
}

function offsetDate(days) {
  const d = new Date()
  d.setDate(d.getDate() - days)
  return d.toISOString().split('T')[0]
}

function calcRange(p) {
  const t = today()
  switch (p) {
    case '1d': return { start: t, end: t }
    case '7d': return { start: offsetDate(6), end: t }
    case '30d': return { start: offsetDate(29), end: t }
    case '90d': return { start: offsetDate(89), end: t }
    case 'all': return { start: null, end: null }
  }
}

function selectPeriod(p) {
  period.value = p
  const { start, end } = calcRange(p)
  emit('update:startDate', start)
  emit('update:endDate', end)
}

function showCustom() {
  period.value = 'custom'
}

function hideCustom() {
  period.value = '7d'
  selectPeriod('7d')
}

function onCustomChange(val) {
  if (val && val.length === 2) {
    emit('update:startDate', val[0])
    emit('update:endDate', val[1])
  }
}

// 初始化：props 有初始值时用 props，否则默认 7d
watch([() => props.startDate, () => props.endDate], ([s, e]) => {
  if (s && e) {
    customRange.value = [s, e]
  }
}, { immediate: true })
</script>

<style scoped>
.period-selector { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.period-buttons { display: flex; gap: 4px; align-items: center; }
.period-custom { display: flex; gap: 8px; align-items: center; }
</style>
```

---

## Task 2: Dashboard.vue 接入卡片1（价格走势 + 涨跌排行）

**Files:**
- Modify: `frontend/src/views/Dashboard.vue:20-29`（替换卡片1 header 中的 date-picker + el-select）
- Modify: `frontend/src/views/Dashboard.vue:464-491`（替换 filter1DateRange、compareDays 变量）
- Modify: `frontend/src/views/Dashboard.vue:871-888`（loadLineChartData 中的日期计算逻辑）
- Modify: `frontend/src/views/Dashboard.vue:975-988`（loadRankingData 中的日期计算逻辑）

### Step 1: 替换卡片1 header 模板

找到第 20-34 行，替换：
```vue
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
```
替换为：
```vue
<PeriodSelector v-model:startDate="filter1Start" v-model:endDate="filter1End" />
```

### Step 2: 替换 filter1DateRange 和 compareDays 变量

找到第 464 行附近：
```
const filter1DateRange = ref([])
```
替换为：
```
const filter1Start = ref(null)
const filter1End = ref(null)
```

找到第 490 行：
```
const compareDays = ref(7)
```
删除此行（不再需要）。

### Step 3: 修改 loadLineChartData 日期逻辑

找到第 871-888 行，当前逻辑：
```javascript
let days = compareDays.value
if (filter1DateRange.value && filter1DateRange.value.length === 2) {
  const start = new Date(filter1DateRange.value[0])
  const end = new Date(filter1DateRange.value[1])
  days = Math.max(7, Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1)
}
```
替换为：
```javascript
let days = 7
if (filter1Start.value && filter1End.value) {
  const start = new Date(filter1Start.value)
  const end = new Date(filter1End.value)
  days = Math.max(1, Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1)
} else if (!filter1Start.value && !filter1End.value) {
  // all mode: days 不限制，后端会查全部
  days = 9999
}
```

同时在 `priceApi.getBenchmarkHistoryMulti` 调用参数中，将 `days` 替换为 `start_date: filter1Start.value, end_date: filter1End.value`。

### Step 4: 修改 loadRankingData 日期逻辑

找到第 975-988 行，当前：
```javascript
let days = compareDays.value
if (filter1DateRange.value && filter1DateRange.value.length === 2) {
  const start = new Date(filter1DateRange.value[0])
  const end = new Date(filter1DateRange.value[1])
  days = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1
}
const params = { limit: 10, days, source: ..., industry: ... }
```
替换为：
```javascript
let days = 7
if (filter1Start.value && filter1End.value) {
  const start = new Date(filter1Start.value)
  const end = new Date(filter1End.value)
  days = Math.max(1, Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1)
} else if (!filter1Start.value && !filter1End.value) {
  days = 9999
}
const params = { limit: 10, days, source: ..., industry: ... }
```

### Step 5: 添加 watch 监听

找到 `watch(filter1Source, () => { loadFilter1Charts() })`（第468行附近），在下面添加：
```javascript
watch([filter1Start, filter1End], () => { loadFilter1Charts() })
```

### Step 6: 在 import 区添加 PeriodSelector

在 `<script setup>` 的 import 区域添加：
```javascript
import PeriodSelector from '../components/PeriodSelector.vue'
```

---

## Task 3: Dashboard.vue 接入卡片2（价格分布饼图）

**Files:**
- Modify: `frontend/src/views/Dashboard.vue:112-121`（替换 filter2DateRange）
- Modify: `frontend/src/views/Dashboard.vue:472-477`（替换 filter2DateRange 变量 + 添加 watch）
- Modify: `frontend/src/views/Dashboard.vue:1026-1035`（loadDistributionData 中的日期逻辑）

### Step 1: 替换卡片2 header 模板

找到第 112-121 行，替换：
```vue
<el-date-picker
  v-model="filter2DateRange"
  type="daterange"
  range-separator="至"
  start-placeholder="开始"
  end-placeholder="结束"
  size="small"
  style="width: 180px"
/>
```
替换为：
```vue
<PeriodSelector v-model:startDate="filter2Start" v-model:endDate="filter2End" />
```

### Step 2: 替换 filter2DateRange 变量 + 添加 watch

找到第 472 行附近：
```
const filter2DateRange = ref([])
```
替换为：
```
const filter2Start = ref(null)
const filter2End = ref(null)
```

在 `watch(filter2Source, () => { loadFilter2Charts() })` 下添加：
```javascript
watch([filter2Start, filter2End], () => { loadFilter2Charts() })
```

### Step 3: 修改 loadDistributionData 日期逻辑

找到第 1026-1035 行，当前：
```javascript
const params = {
  days: 30,
  source: filter2Source.value || null,
  category_id: null,
  subcategory_id: null,
  industry: filter2Industry.value || null
}
```
替换为：
```javascript
let days = 30
if (filter2Start.value && filter2End.value) {
  const start = new Date(filter2Start.value)
  const end = new Date(filter2End.value)
  days = Math.max(1, Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1)
} else if (!filter2Start.value && !filter2End.value) {
  days = 9999
}
const params = {
  days,
  source: filter2Source.value || null,
  category_id: null,
  subcategory_id: null,
  industry: filter2Industry.value || null
}
```

---

## Task 4: Dashboard.vue 接入卡片3（供应商看板）

**Files:**
- Modify: `frontend/src/views/Dashboard.vue:501`（替换 supplierComparisonDays 变量）
- Modify: `frontend/src/views/Dashboard.vue:1066-1072`（loadSupplierComparison 中的日期逻辑）

### Step 1: 添加 PeriodSelector 到卡片3

在卡片3的 header controls 区域（第110行附近 filter2Source 后面）添加：
```vue
<PeriodSelector v-model:startDate="supplierStart" v-model:endDate="supplierEnd" />
```

### Step 2: 替换 supplierComparisonDays 变量

找到第 501 行：
```
const supplierComparisonDays = ref(30)
```
删除此行（不再需要）。

### Step 3: 修改 loadSupplierComparison 日期逻辑

找到第 1066-1072 行，当前：
```javascript
const params = {
  days: supplierComparisonDays.value,
  source: filter2Source.value || null,
  industry: filter3Industry.value || null
}
```
替换为：
```javascript
let days = 30
if (supplierStart.value && supplierEnd.value) {
  const start = new Date(supplierStart.value)
  const end = new Date(supplierEnd.value)
  days = Math.max(1, Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1)
} else if (!supplierStart.value && !supplierEnd.value) {
  days = 9999
}
const params = {
  days,
  source: filter3Source.value || null,
  industry: filter3Industry.value || null
}
```

### Step 4: 添加变量声明

在第 501 行附近（删除 supplierComparisonDays 的位置）添加：
```
const supplierStart = ref(null)
const supplierEnd = ref(null)
```

### Step 5: 添加 watch

在 `watch(filter3Industry, () => { loadSupplierComparison() })` 下添加：
```javascript
watch([supplierStart, supplierEnd], () => { loadSupplierComparison() })
```

---

## Task 5: 删除 Dashboard.vue 废弃代码

### Step 1: 删除 expandChartDays

找到第 491 行：
```
const expandChartDays = ref(7)
```
删除此行。

### Step 2: 删除 filter1DateRange 和 filter2DateRange 的 watch（如果存在）

搜索文件中是否有 `watch(filter1DateRange` 和 `watch(filter2DateRange`，若有则删除。

### Step 3: 确认没有遗漏

搜索 `compareDays`、`filter1DateRange`、`filter2DateRange`、`supplierComparisonDays`、`expandChartDays`，确认无残留引用。

---

## Task 6: ProductCompare.vue 替换时间筛选

**Files:**
- Modify: `frontend/src/views/ProductCompare.vue:49-72`（替换 date-row）
- Modify: `frontend/src/views/ProductCompare.vue:125-168`（删除废弃变量和函数）
- Modify: `frontend/src/views/ProductCompare.vue:196-199`（修改 loadComparison 中的日期逻辑）

### Step 1: 替换 date-row 模板

找到第 49-72 行，替换：
```vue
<div class="date-row">
  <span class="date-label">时间范围</span>
  <div class="date-buttons">
    <el-button
      v-for="d in datePresets"
      :key="d"
      :type="selectedDays === d ? 'primary' : 'default'"
      size="small"
      @click="setDateDays(d)"
    >{{ d }}天</el-button>
    <el-button size="small" @click="showCustomDate = true">自定义</el-button>
  </div>
  <el-date-picker
    v-if="showCustomDate"
    v-model="dateRange"
    type="daterange"
    range-separator="至"
    start-placeholder="开始"
    end-placeholder="结束"
    size="small"
    style="width: 220px; margin-left: 8px"
    @change="loadComparison"
  />
</div>
```
替换为：
```vue
<div class="date-row">
  <span class="date-label">时间范围</span>
  <PeriodSelector v-model:startDate="compareStart" v-model:endDate="compareEnd" />
</div>
```

### Step 2: 替换废弃变量

找到第 125-128 行：
```javascript
const dateRange = ref(null)
const datePresets = [7, 30, 60, 90]
const selectedDays = ref(30)
const showCustomDate = ref(false)
```
替换为：
```javascript
const compareStart = ref(null)
const compareEnd = ref(null)
```

### Step 3: 删除 setDateDays 函数

找到第 163-168 行的 `setDateDays` 函数，删除整个函数。

### Step 4: 修改 loadComparison 日期逻辑

找到第 196-199 行，当前：
```javascript
if (dateRange.value && dateRange.value.length === 2) {
  const start = new Date(dateRange.value[0])
  const end = new Date(dateRange.value[1])
  days = Math.ceil((end - start) / (1000 * 60 * 60 * 24))
  if (days < 1) days = 1
}
```
替换为：
```javascript
if (compareStart.value && compareEnd.value) {
  const start = new Date(compareStart.value)
  const end = new Date(compareEnd.value)
  days = Math.max(1, Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1)
} else if (!compareStart.value && !compareEnd.value) {
  // all mode
  days = 9999
}
```

### Step 5: 添加 watch

在 `watch(selectedIndustry, ...)` 附近添加：
```javascript
watch([compareStart, compareEnd], () => { loadComparison() })
```

### Step 6: import PeriodSelector

在 import 区域添加：
```javascript
import PeriodSelector from '../components/PeriodSelector.vue'
```

### Step 7: 清理 CSS

删除 `.date-buttons` 和 `.date-label` 相关样式（如有独立样式）。

---

## Task 7: ReportView.vue 周报模式接入

**Files:**
- Modify: `frontend/src/views/ReportView.vue:34-39`（替换 startDate/endDate pickers）
- Modify: `frontend/src/views/ReportView.vue:183`（loadStats 中的日期参数）

### Step 1: 替换 startDate/endDate pickers

找到第 34-39 行：
```vue
<el-form-item label="开始日期" v-if="reportType === 'weekly'">
  <el-date-picker v-model="startDate" type="date" value-format="YYYY-MM-DD" placeholder="选择开始日期" />
</el-form-item>
<el-form-item label="结束日期" v-if="reportType === 'weekly'">
  <el-date-picker v-model="endDate" type="date" value-format="YYYY-MM-DD" placeholder="选择结束日期" />
</el-form-item>
```
替换为：
```vue
<el-form-item label="日期范围" v-if="reportType === 'weekly'">
  <PeriodSelector v-model:startDate="reportStart" v-model:endDate="reportEnd" />
</el-form-item>
```

### Step 2: 修改 loadStats 参数

找到第 183 行：
```javascript
const params = { start_date: s, end_date: e, limit: 1000 }
```
这里 `s, e` 来自 `getEffectiveDates()`。修改 `getEffectiveDates()` 函数逻辑，当 `reportType === 'weekly'` 时使用 `reportStart/reportEnd`，当 `reportType === 'monthly'` 时使用 `month`。

或者更简单的方式：在 `loadStats()` 内部直接判断：
```javascript
let s = null, e = null
if (reportType.value === 'weekly') {
  s = reportStart.value
  e = reportEnd.value
}
const params = { start_date: s, end_date: e, limit: 1000 }
```

### Step 3: import PeriodSelector

在 import 区域添加：
```javascript
import PeriodSelector from '../components/PeriodSelector.vue'
```

---

## Task 8: 验证与测试

### Step 1: 启动前端开发服务器

```bash
cd frontend && npm run dev
```

### Step 2: 验证 Dashboard 三个卡片

- 卡片1：切换 1d/7d/30d/90d/all，确认折线图和柱状图数据随时间范围变化
- 卡片2：切换不同时间范围，确认饼图数据变化
- 卡片3：切换时间范围，确认供应商对比数据变化
- 三个卡片彼此独立，互不影响

### Step 3: 验证 ProductCompare

- 切换 1d/7d/30d/90d/all，确认对比图表数据变化
- 点击「自定义」，选一个日期范围，确认图表变化

### Step 4: 验证 ReportView

- 切换周报模式，选择日期范围，点击「查询数据」，确认统计数据变化

---

## Task 9: 提交代码

```bash
git add frontend/src/components/PeriodSelector.vue \
       frontend/src/views/Dashboard.vue \
       frontend/src/views/ProductCompare.vue \
       frontend/src/views/ReportView.vue
git commit -m "feat: add unified PeriodSelector component, replace scattered date filters"
```
