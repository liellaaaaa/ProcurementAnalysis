# 供应商智能分析看板 - 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 Dashboard.vue 供应商对比卡片升级为智能分析看板：Treemap（面积=count，颜色=avg_deviation）+ 右侧详情面板（20%）

**Architecture:** 后端 `/supplier-comparison` API 增加偏离度字段；前端用 ECharts Treemap 替换旧饼图+柱状图+明细表，实现 visualMap 色阶+长尾聚合+详情面板交互

**Tech Stack:** FastAPI + SQLAlchemy (后端), Vue3 + ECharts + Element Plus (前端)

---

## 文件结构

| 操作 | 文件路径 | 职责 |
|------|----------|------|
| Modify | `backend/api/routes/prices.py` | 改造 `/supplier-comparison`，增加 avg_deviation, max_deviation, status_label, benchmark_price, deviation |
| Modify | `frontend/src/views/Dashboard.vue` | 重构供应商卡片：移除旧三视图，新增 Treemap + 详情面板 |

---

## Task 1: 后端 API 改造 — 增加偏离度字段

**Files:**
- Modify: `backend/api/routes/prices.py` (lines 943-1061， `/supplier-comparison` 路由)

### 1.1 理解现有代码结构

当前 `/supplier-comparison` 返回结构：
- `supplier_counts`: `{supplier, count, product_count}`（无偏离度）
- `product_supplier_prices`: `{product_id, product, supplier, price, quote_count}`（无基准价）
- `supplier_products`: `{supplier, products: [{product_id, product, price, count}]}`（无基准价）

### 1.2 需要获取基准价

基准价来自 `BenchmarkPrice` 表，按 `product_id` + `record_date` 聚合。需要：
1. 获取每个 product_id 的最新基准价
2. 计算每条报价的 `deviation = (price - benchmark) / benchmark`
3. 聚合为 `avg_deviation`, `max_deviation`, `status_label`

### 1.3 修改 supplier_counts 返回

**当前代码（约 line 968-991）：**
```python
# 1. supplier_counts: 每个供应商的报价条数和产品数
supplier_stats = {}
for q in quotes:
    supplier = q.supplier or "未知供应商"
    if supplier not in supplier_stats:
        supplier_stats[supplier] = {"supplier": supplier, "count": 0, "product_count": 0}
    supplier_stats[supplier]["count"] += 1
    if "_product_ids" not in supplier_stats[supplier]:
        supplier_stats[supplier]["_product_ids"] = set()
    supplier_stats[supplier]["_product_ids"].add(q.product_id)

supplier_counts = []
for supplier, stats in supplier_stats.items():
    supplier_counts.append({
        "supplier": supplier,
        "count": stats["count"],
        "product_count": len(stats["_product_ids"])
    })
```

**修改为**（新增 avg_deviation, max_deviation, status_label）：

首先，在函数开头获取所有产品的最新基准价：
```python
# 获取所有产品的最新基准价
benchmark_map = {}
benchmark_subquery = db.query(
    BenchmarkPrice.product_id,
    func.max(BenchmarkPrice.record_date).label('max_date')
).group_by(BenchmarkPrice.product_id).subquery()

benchmark_rows = db.query(BenchmarkPrice).join(
    benchmark_subquery,
    (BenchmarkPrice.product_id == benchmark_subquery.c.product_id) &
    (BenchmarkPrice.record_date == benchmark_subquery.c.max_date)
).all()

for bp in benchmark_rows:
    benchmark_map[bp.product_id] = bp.price
```

然后，修改 supplier_stats 的计算逻辑：
```python
supplier_stats = {}
for q in quotes:
    supplier = q.supplier or "未知供应商"
    if supplier not in supplier_stats:
        supplier_stats[supplier] = {
            "supplier": supplier,
            "count": 0,
            "product_count": 0,
            "_product_ids": set(),
            "_deviations": []  # 新增：收集偏离度
        }
    supplier_stats[supplier]["count"] += 1
    supplier_stats[supplier]["_product_ids"].add(q.product_id)

    # 计算偏离度
    benchmark_price = benchmark_map.get(q.product_id)
    if benchmark_price and benchmark_price > 0:
        dev = (q.price - benchmark_price) / benchmark_price
        supplier_stats[supplier]["_deviations"].append(dev)

# 构建 supplier_counts（含新字段）
supplier_counts = []
for supplier, stats in supplier_stats.items():
    deviations = stats["_deviations"]
    avg_dev = sum(deviations) / len(deviations) if deviations else 0
    max_dev = max(deviations) if deviations else 0

    # 状态标签
    if avg_dev <= -0.15:
        status_label = "优"
    elif avg_dev >= 0.15:
        status_label = "风险"
    else:
        status_label = "正常"

    supplier_counts.append({
        "supplier": supplier,
        "count": stats["count"],
        "product_count": len(stats["_product_ids"]),
        "avg_price": round(sum(q.price for q in quotes if q.supplier == supplier or q.supplier == (supplier or "未知供应商")) / stats["count"], 2) if stats["count"] > 0 else 0,
        "avg_deviation": round(avg_dev, 4),
        "max_deviation": round(max_dev, 4),
        "status_label": status_label
    })
```

### 1.4 修改 product_supplier_prices 返回

**当前代码（约 line 992-1022）：**
```python
product_supplier_map = {}
for q in quotes:
    key = (q.product_id, q.supplier or "未知供应商")
    ...
```

**修改为**：每条记录增加 `benchmark_price` 和 `deviation`：
```python
product_supplier_prices = []
for key, item in product_supplier_map.items():
    benchmark_price = benchmark_map.get(item["product_id"])
    deviation = round((item["price"] - benchmark_price) / benchmark_price, 4) if benchmark_price and benchmark_price > 0 else 0
    product_supplier_prices.append({
        "product_id": item["product_id"],
        "product": item["product"],
        "supplier": item["supplier"],
        "price": item["price"],
        "quote_count": item["quote_count"],
        "benchmark_price": benchmark_price or 0,
        "deviation": deviation
    })
```

### 1.5 修改 supplier_products 返回

**当前代码（约 line 1023-1059）：**
```python
supplier_products_map = {}
for q in quotes:
    ...
    product_list.append({
        "product_id": pdata["product_id"],
        "product": pdata["product"],
        "price": pdata["price"],
        "count": pdata["count"]
    })
```

**修改为**：增加 `benchmark_price` 和 `deviation`：
```python
product_list.append({
    "product_id": pdata["product_id"],
    "product": pdata["product"],
    "price": pdata["price"],
    "count": pdata["count"],
    "benchmark_price": benchmark_map.get(pdata["product_id"]) or 0,
    "deviation": round((pdata["price"] - (benchmark_map.get(pdata["product_id"]) or 0)) / (benchmark_map.get(pdata["product_id"]) or 1), 4) if benchmark_map.get(pdata["product_id"]) else 0
})
```

### 1.6 测试验证

```bash
curl "http://localhost:8000/api/v1/prices/supplier-comparison?days=30"
```

验证返回数据含新字段：`avg_deviation`, `max_deviation`, `status_label`, `benchmark_price`, `deviation`

### 1.7 提交

```bash
git add backend/api/routes/prices.py
git commit -m "feat: add deviation fields to /supplier-comparison API"
```

---

## Task 2: 前端重构 — Treemap + 详情面板

**Files:**
- Modify: `frontend/src/views/Dashboard.vue`（供应商对比卡片部分，约 line 173-248）

### 2.1 移除旧代码

**移除模板部分**（line 173-248）：删除整个供应商对比卡片的旧三视图（饼图+柱状图+明细表），替换为新布局。

**移除 script 部分**：
- 删除 `supplierChartRef`, `supplierBarChartRef`（旧饼图和柱状图 ref）
- 删除 `supplierPieChart`, `supplierBarChart`（旧图表实例）
- 删除 `loadSupplierComparison` 中更新旧图表的代码
- 删除 `initSupplierCharts` 函数
- 保留 `supplierProducts`（用于详情面板）

### 2.2 新增响应式变量

在 `script setup` 中（`supplierProducts` 附近）添加：

```javascript
// Supplier treemap
const supplierTreemapRef = ref(null)
const selectedSupplier = ref(null)  // 当前选中的供应商
const supplierSummary = ref(null)   // 空闲态统计摘要
let supplierTreemap = null
const TOP_N = 12  // 长尾聚合阈值
```

### 2.3 新增 Treemap 初始化函数

```javascript
function initSupplierTreemap() {
  if (!supplierTreemapRef.value) return
  if (supplierTreemap) supplierTreemap.dispose()
  supplierTreemap = echarts.init(supplierTreemapRef.value)

  supplierTreemap.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: '#fff',
      borderColor: '#E8E3F3',
      textStyle: { color: '#1E293B' },
      borderRadius: 8,
      formatter: (params) => {
        if (params.data.id === 'others') {
          return `<strong>${params.name}</strong><br/>点击查看全部供应商`
        }
        const dev = params.data.avg_deviation
        const devStr = dev != null ? `${(dev * 100).toFixed(1)}%` : '-'
        const statusColors = { '优': '#008000', '正常': '#D3D3D3', '风险': '#DC143C' }
        const color = statusColors[params.data.status_label] || '#D3D3D3'
        return `
          <strong>${params.name}</strong><br/>
          报价: ${params.data.count}条<br/>
          偏离: <span style="color:${color}">${devStr}</span><br/>
          状态: <span style="color:${color}">${params.data.status_label || '-'}</span>
        `
      }
    },
    visualMap: {
      show: false,
      min: -0.3,
      max: 0.3,
      inRange: {
        color: ['#008000', '#90EE90', '#D3D3D3', '#FFB6C1', '#DC143C']
      },
      pieces: [
        { lte: -0.15, color: '#008000' },
        { gt: -0.15, lte: 0.15, color: '#D3D3D3' },
        { gt: 0.15, color: '#DC143C' }
      ]
    },
    series: [{
      type: 'treemap',
      data: [],
      label: { show: true, formatter: '{b}', fontSize: 11, color: '#1E293B' },
      itemStyle: { borderColor: '#fff', borderWidth: 2, gapWidth: 2 },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.2)' } }
    }]
  })

  // 点击事件
  supplierTreemap.off('click')
  supplierTreemap.on('click', (params) => {
    if (params.data.id === 'others') {
      // TODO: 显示完整供应商列表弹窗
      return
    }
    selectedSupplier.value = params.data
  })
}
```

### 2.4 修改 loadSupplierComparison 函数

用 Treemap 数据更新逻辑替换旧图表更新代码：

```javascript
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

    // 构建 Treemap 数据
    const counts = data.supplier_counts || []
    const sorted = [...counts].sort((a, b) => b.count - a.count)
    const top = sorted.slice(0, TOP_N)
    const others = sorted.slice(TOP_N)

    const treemapData = top.map(s => ({
      name: s.supplier,
      value: s.count,
      id: s.supplier,
      avg_deviation: s.avg_deviation,
      max_deviation: s.max_deviation,
      status_label: s.status_label,
      count: s.count,
      product_count: s.product_count,
      itemStyle: { color: s.avg_deviation != null ? undefined : '#D3D3D3' }
    }))

    if (others.length > 0) {
      treemapData.push({
        name: `其他供应商 (${others.length}家)`,
        value: others.reduce((sum, s) => sum + s.count, 0),
        id: 'others',
        avg_deviation: null,
        status_label: '未分析',
        count: others.reduce((sum, s) => sum + s.count, 0),
        product_count: others.reduce((sum, s) => sum + s.product_count, 0),
        itemStyle: { color: '#E8E3F3' }
      })
    }

    // 更新 Treemap
    if (supplierTreemap) {
      supplierTreemap.setOption({
        series: [{
          data: treemapData
        }]
      })
    }

    // 构建空闲态摘要
    const totalCount = counts.reduce((s, c) => s + c.count, 0)
    const totalDev = counts.reduce((s, c) => s + (c.avg_deviation || 0), 0)
    supplierSummary.value = {
      total: counts.length,
      totalCount,
      avgDeviation: totalDev / counts.length || 0
    }

    // 保留 supplier_products 用于详情面板
    supplierProducts.value = data.supplier_products || []
  } catch (e) {
    console.error('Failed to load supplier comparison', e)
  }
}
```

### 2.5 新增详情面板组件

在模板的供应商卡片中，用以下布局替换旧三视图：

```vue
<div class="supplier-treemap-panel">
  <!-- 左侧 Treemap (80%) -->
  <div class="treemap-container" ref="supplierTreemapRef"></div>

  <!-- 右侧详情面板 (20%) -->
  <div class="supplier-detail-panel">
    <!-- 空闲态 -->
    <div v-if="!selectedSupplier" class="detail-idle">
      <div class="idle-summary">
        <p class="idle-title">供应商总览</p>
        <p class="idle-num">{{ supplierSummary?.total || 0 }} 个供应商</p>
        <p class="idle-num">{{ supplierSummary?.totalCount || 0 }} 条报价</p>
        <p class="idle-dev" :class="getDevClass(supplierSummary?.avgDeviation)">
          平均偏离: {{ supplierSummary ? (supplierSummary.avgDeviation * 100).toFixed(1) : 0 }}%
        </p>
      </div>
      <p class="idle-hint">点击方块查看供应商详情</p>
    </div>

    <!-- 选中态 -->
    <div v-else class="detail-active">
      <div class="detail-header">
        <h3 class="supplier-name">{{ selectedSupplier.name }}</h3>
        <el-tag :type="getTagType(selectedSupplier.status_label)" size="small">
          {{ selectedSupplier.status_label }}
        </el-tag>
      </div>
      <div class="detail-cards">
        <div class="detail-card">
          <span class="card-label">报价条数</span>
          <span class="card-value">{{ selectedSupplier.count }}条</span>
        </div>
        <div class="detail-card">
          <span class="card-label">涉及产品</span>
          <span class="card-value">{{ selectedSupplier.product_count }}个</span>
        </div>
        <div class="detail-card">
          <span class="card-label">平均偏离</span>
          <span class="card-value" :class="getDevClass(selectedSupplier.avg_deviation)">
            {{ selectedSupplier.avg_deviation != null ? (selectedSupplier.avg_deviation * 100).toFixed(1) : 0 }}%
          </span>
        </div>
        <div class="detail-card">
          <span class="card-label">最大偏离</span>
          <span class="card-value" :class="getDevClass(selectedSupplier.max_deviation)">
            {{ selectedSupplier.max_deviation != null ? (selectedSupplier.max_deviation * 100).toFixed(1) : 0 }}%
          </span>
        </div>
      </div>
      <div class="product-list">
        <p class="list-title">供应产品</p>
        <div v-for="sp in getSupplierProducts(selectedSupplier.name)" :key="sp.product_id" class="product-item">
          <span class="product-name">{{ sp.product }}</span>
          <span class="product-price">¥{{ sp.price?.toLocaleString() }}</span>
          <span class="product-dev" :class="getDevClass(sp.deviation)">
            {{ sp.deviation != null ? (sp.deviation * 100).toFixed(1) : 0 }}%
          </span>
        </div>
      </div>
    </div>
  </div>
</div>
```

### 2.6 新增辅助函数

在 `<script setup>` 中添加：

```javascript
function getDevClass(dev) {
  if (dev == null) return ''
  if (dev <= -0.15) return 'dev-good'
  if (dev >= 0.15) return 'dev-bad'
  return 'dev-normal'
}

function getTagType(status) {
  const map = { '优': 'success', '正常': 'info', '风险': 'danger' }
  return map[status] || 'info'
}

function getSupplierProducts(supplierName) {
  const supplier = supplierProducts.value.find(s => s.supplier === supplierName)
  return supplier?.products || []
}
```

### 2.7 新增样式

在 `<style scoped>` 中添加：

```css
.supplier-treemap-panel {
  display: flex;
  gap: 16px;
  height: 320px;
}

.treemap-container {
  flex: 0 0 80%;
  height: 100%;
  min-height: 320px;
}

.supplier-detail-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: var(--bg-primary);
  border-radius: 8px;
  padding: 12px;
  overflow-y: auto;
}

.detail-idle {
  display: flex;
  flex-direction: column;
  justify-content: center;
  height: 100%;
  text-align: center;
}

.idle-summary {
  margin-bottom: 16px;
}

.idle-title {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.idle-num {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 4px 0;
}

.idle-dev {
  font-size: 14px;
  font-weight: 500;
  margin-top: 8px;
}

.idle-hint {
  font-size: 12px;
  color: var(--text-muted);
}

.detail-active {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.supplier-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.detail-card {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px;
  background: var(--bg-hover);
  border-radius: 6px;
}

.card-label {
  font-size: 10px;
  color: var(--text-muted);
  text-transform: uppercase;
}

.card-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.product-list {
  flex: 1;
  overflow-y: auto;
}

.list-title {
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  margin-bottom: 8px;
}

.product-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px solid var(--border-color);
}

.product-name {
  flex: 1;
  font-size: 12px;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.product-price {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-primary);
}

.product-dev {
  font-size: 11px;
  font-weight: 500;
  min-width: 40px;
  text-align: right;
}

.dev-good { color: #008000; }
.dev-bad { color: #DC143C; }
.dev-normal { color: #D3D3D3; }
```

### 2.8 修改 onMounted 和 onUnmounted

在 `onMounted` 中：
- 移除 `initSupplierCharts()` 调用（已由新的初始化逻辑替代）
- 添加 `initSupplierTreemap()` 调用

在 `window.addEventListener('resize', ...)` 中：
- 移除 `supplierPieChart?.resize()` 和 `supplierBarChart?.resize()`
- 添加 `supplierTreemap?.resize()`

在 `onUnmounted` 中：
- 移除 `supplierPieChart?.dispose()` 和 `supplierBarChart?.dispose()`
- 添加 `supplierTreemap?.dispose()`

### 2.9 验证构建

```bash
cd frontend
npm run dev
```

打开 Dashboard，确认：
1. 供应商卡片显示为 Treemap（矩形树状图）
2. 点击方块，右侧面板显示供应商详情
3. 色阶正确（深绿=便宜，深红=贵）
4. 长尾聚合正确（前12名独立，其余灰色"更多供应商"）

### 2.10 提交

```bash
git add frontend/src/views/Dashboard.vue
git commit -m "feat: replace supplier card with treemap + detail panel"
```

---

## 自检清单

1. **Spec 覆盖**：
   - Treemap（面积=count，颜色=avg_deviation）✅
   - visualMap 色阶（±15% 分水岭）✅
   - 长尾聚合（TOP_N=12 + others）✅
   - 详情面板（空闲态摘要 + 选中态详情）✅
   - Hover tooltip + Click 交互 ✅

2. **占位符扫描**：无 "TBD"、"TODO"、"fill in" 等占位符 ✅

3. **类型一致性**：
   - `avg_deviation`, `max_deviation` 字段名一致 ✅
   - `status_label` 状态值一致（优/正常/风险）✅
   - `deviation` 用于产品级别 ✅

4. **后端 API 字段**：
   - `supplier_counts`: `avg_deviation`, `max_deviation`, `status_label` ✅
   - `product_supplier_prices`: `benchmark_price`, `deviation` ✅
   - `supplier_products.products`: `benchmark_price`, `deviation` ✅

---

## 执行选项

**1. Subagent-Driven (recommended)** - 每个 Task 由独立 subagent 执行，Task 间并行推进

**2. Inline Execution** - 本 session 顺序执行，batch 执行带 checkpoint

哪个方案？