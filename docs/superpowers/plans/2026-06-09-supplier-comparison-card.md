# 供应商对比卡片 - 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 Dashboard.vue 中新增供应商对比卡片，包含供应商报价数量饼图、同一产品多供应商价格对比柱状图、供应商-产品明细表。

**Architecture:** 后端新增 `/api/v1/prices/supplier-comparison` 接口从 `DetailedQuote` 表聚合供应商数据，前端新增 API 方法调用该接口，Dashboard 新增第四张卡片渲染三个视图。

**Tech Stack:** FastAPI + SQLAlchemy (后端), Vue3 + ECharts + Element Plus (前端)

---

## 文件结构

| 操作 | 文件路径 | 职责 |
|------|----------|------|
| Modify | `backend/api/routes/prices.py` | 新增 `/supplier-comparison` 端点 |
| Modify | `frontend/src/api/price.js` | 新增 `getSupplierComparison` API 方法 |
| Modify | `frontend/src/views/Dashboard.vue` | 新增供应商对比卡片（第四张卡片） |

---

## Task 1: 后端新增供应商对比 API

**Files:**
- Modify: `backend/api/routes/prices.py` (在 `get_dashboard_volatility` 之后添加新路由，约第 940 行)

- [ ] **Step 1: 添加 supplier-comparison 路由**

在 `prices.py` 末尾（`get_dashboard_volatility` 路由之后）添加：

```python
@router.get("/supplier-comparison")
async def get_supplier_comparison(
    product_id: Optional[int] = None,
    days: int = Query(30, ge=1, le=365),
    source: Optional[str] = None,
    industry: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取供应商对比数据：报价数量 + 同一产品多供应商价格对比"""
    from datetime import date, timedelta
    from backend.models.database import DetailedQuote, Product

    start_date = (date.today() - timedelta(days=days)).isoformat()

    # 构建基础查询
    query = db.query(
        DetailedQuote.supplier,
        DetailedQuote.product_id,
        Product.product_name,
        func.count(DetailedQuote.id).label('quote_count'),
        func.max(DetailedQuote.publish_date).label('latest_date')
    ).join(Product, DetailedQuote.product_id == Product.id).filter(
        DetailedQuote.publish_date >= start_date
    )

    if source and source != '__all__':
        query = query.filter(DetailedQuote.source == source)
    if industry:
        query = query.filter(Product.industry == industry)
    if product_id:
        query = query.filter(DetailedQuote.product_id == product_id)

    # 按 supplier + product_id 分组，取最新价格
    group_results = query.group_by(
        DetailedQuote.supplier,
        DetailedQuote.product_id,
        Product.product_name
    ).all()

    # 构建 supplier_counts: 每个供应商的报价数和产品数
    supplier_stats = {}
    for supplier, pid, pname, qcount, latest_date in group_results:
        if supplier not in supplier_stats:
            supplier_stats[supplier] = {"count": 0, "product_count": 0, "products": set()}
        supplier_stats[supplier]["count"] += qcount
        supplier_stats[supplier]["products"].add(pid)

    supplier_counts = [
        {
            "supplier": s,
            "count": stats["count"],
            "product_count": len(stats["products"])
        }
        for s, stats in supplier_stats.items()
    ]

    # 获取每个供应商-产品对的最新报价（取价格最高的）
    latest_prices_query = db.query(
        DetailedQuote.supplier,
        DetailedQuote.product_id,
        Product.product_name,
        func.max(DetailedQuote.price).label('max_price'),
        func.count(DetailedQuote.id).label('quote_count')
    ).join(Product, DetailedQuote.product_id == Product.id).filter(
        DetailedQuote.publish_date >= start_date
    )

    if source and source != '__all__':
        latest_prices_query = latest_prices_query.filter(DetailedQuote.source == source)
    if industry:
        latest_prices_query = latest_prices_query.filter(Product.industry == industry)
    if product_id:
        latest_prices_query = latest_prices_query.filter(DetailedQuote.product_id == product_id)

    price_results = latest_prices_query.group_by(
        DetailedQuote.supplier,
        DetailedQuote.product_id,
        Product.product_name
    ).all()

    product_supplier_prices = [
        {
            "product_id": pid,
            "product": pname,
            "supplier": s,
            "price": float(price),
            "quote_count": qcount
        }
        for s, pid, pname, price, qcount in price_results
    ]

    # 构建 supplier_products: 每个供应商供应的产品列表
    supplier_products_map = {}
    for s, pid, pname, qcount, latest_date in group_results:
        if s not in supplier_products_map:
            supplier_products_map[s] = {}
        if pid not in supplier_products_map[s]:
            # 获取该供应商该产品的最新价格
            latest_price = db.query(func.max(DetailedQuote.price)).filter(
                DetailedQuote.supplier == s,
                DetailedQuote.product_id == pid
            ).scalar() or 0
            supplier_products_map[s][pid] = {
                "product_id": pid,
                "product": pname,
                "price": float(latest_price),
                "count": 0
            }
        supplier_products_map[s][pid]["count"] += qcount

    supplier_products = [
        {
            "supplier": s,
            "products": list(products.values())
        }
        for s, products in supplier_products_map.items()
    ]

    return {
        "supplier_counts": supplier_counts,
        "product_supplier_prices": product_supplier_prices,
        "supplier_products": supplier_products
    }
```

- [ ] **Step 2: 注册路由（确认已挂载）**

检查 `prices.py` 顶部的 `router = APIRouter(prefix="/api/v1/prices", tags=["价格数据"])` — 新路由已使用同一 router，无需额外注册。

- [ ] **Step 3: 启动后端验证 API**

```bash
cd C:\Users\langwan\Desktop\ProcurementAnalysis
venv\Scripts\activate
uvicorn backend.main:app --reload --port 8000
```

在另一个终端测试：
```bash
curl "http://localhost:8000/api/v1/prices/supplier-comparison"
```
预期：返回 JSON 含 `supplier_counts`, `product_supplier_prices`, `supplier_products` 三个字段。

- [ ] **Step 4: 提交**

```bash
git add backend/api/routes/prices.py
git commit -m "feat: add /prices/supplier-comparison API for supplier comparison card"
```

---

## Task 2: 前端新增 API 方法

**Files:**
- Modify: `frontend/src/api/price.js` (在文件末尾 `getBenchmarkHistoryMulti` 之后添加新方法)

- [ ] **Step 1: 添加 getSupplierComparison 方法**

在 `price.js` 的 `getBenchmarkHistoryMulti` 之后添加：

```javascript
getSupplierComparison(params) {
  // params: { product_id, days, source, industry }
  return api.get('/prices/supplier-comparison', { params })
}
```

完整文件检查：`frontend/src/api/price.js` 目前以 `export const priceRecordApi = {` 结尾（第 49 行），在 `getBenchmarkHistoryMulti` 之后（第 45 行）插入新方法。

- [ ] **Step 2: 验证文件语法**

```bash
cd frontend
node -e "require('./src/api/price.js')" 2>&1 || echo "Syntax check"
```
（若无错误输出则语法正确）

- [ ] **Step 3: 提交**

```bash
git add frontend/src/api/price.js
git commit -m "feat: add getSupplierComparison API method"
```

---

## Task 3: Dashboard.vue 新增供应商对比卡片

**Files:**
- Modify: `frontend/src/views/Dashboard.vue` (在 Card 2 和 Card 3 之间插入 Card 3)

### 3.1 新增 ref 和响应式变量

在 `script setup` 顶部（约第 344 行 `const expandChartRefs` 附近）添加：

```javascript
// Supplier comparison card
const supplierChartRef = ref(null)
const supplierBarChartRef = ref(null)
const supplierProducts = ref([])
const selectedSupplierProduct = ref(null)
const supplierComparisonDays = ref(30)
let supplierPieChart = null
let supplierBarChart = null
```

### 3.2 新增数据加载函数

在 `loadDistributionData` 函数之后（约第 947 行）添加：

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
    const data = res.data

    // 更新饼图：供应商报价数量
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

    // 更新柱状图：同一产品多供应商价格对比
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

    // 保存数据用于明细表
    supplierProducts.value = data.supplier_products || []
  } catch (e) {
    console.error('Failed to load supplier comparison', e)
  }
}
```

### 3.3 新增图表初始化函数

在 `initBarChart` 之后（约第 1112 行）添加：

```javascript
function initSupplierCharts() {
  // 饼图：供应商报价数量
  if (supplierChartRef.value) {
    if (supplierPieChart) supplierPieChart.dispose()
    supplierPieChart = echarts.init(supplierChartRef.value)
    supplierPieChart.setOption({
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c}条报价 ({d}%)',
        backgroundColor: '#fff',
        borderColor: '#E8E3F3',
        textStyle: { color: '#1E293B' },
        borderRadius: 8
      },
      legend: { orient: 'vertical', left: 'left', top: 'center', textStyle: { color: '#64748B', fontSize: 10 }, itemGap: 6, width: 70 },
      series: [{
        type: 'pie',
        radius: ['28%', '60%'],
        center: ['55%', '50%'],
        label: { show: false },
        emphasis: { label: { show: false } }
      }]
    })
  }

  // 柱状图：供应商价格对比
  if (supplierBarChartRef.value) {
    if (supplierBarChart) supplierBarChart.dispose()
    supplierBarChart = echarts.init(supplierBarChartRef.value)
    supplierBarChart.setOption({
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#fff',
        borderColor: '#E8E3F3',
        textStyle: { color: '#1E293B' },
        axisPointer: { type: 'shadow' },
        borderRadius: 8,
        formatter: (params) => {
          const p = params[0]
          return `<strong>${p.name}</strong><br/>价格: ¥${p.value?.toLocaleString() ?? '-'}`
        }
      },
      grid: { left: '3%', right: '8%', bottom: '3%', top: '3%', containLabel: true },
      xAxis: { type: 'value', axisLine: { show: false }, axisLabel: { color: '#94A3B4' }, splitLine: { lineStyle: { color: '#F0EBF9', type: 'dashed' } } },
      yAxis: { type: 'category', data: [], axisLine: { lineStyle: { color: '#E8E3F3' } }, axisLabel: { color: '#64748B', fontSize: 10 } },
      series: [{ type: 'bar', barWidth: '60%' }]
    })
  }
}
```

### 3.4 在 onMounted 中初始化图表

在 `onMounted` 中（约第 1114 行 `initLineChart()` 之后）添加：

```javascript
initSupplierCharts()
```

并在 `window.addEventListener('resize', ...)` 中添加：

```javascript
supplierPieChart?.resize()
supplierBarChart?.resize()
```

### 3.5 在 loadFilter2Charts 中调用加载函数

在 `loadFilter2Charts` 函数（约第 639 行）中添加：

```javascript
await Promise.all([
  loadDistributionData(),
  loadIndicatorCards(),
  loadSupplierComparison()  // 新增
])
```

### 3.6 新增卡片模板

在 `Dashboard.vue` 的 `<template>` 中，在 Card 2（`</el-card>` 第 171 行附近）和 Card 3（详细数据卡片）之间插入新卡片：

```vue
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
          <span class="price-value">¥{{ Math.max(...row.products.map(p => p.price)).toLocaleString() }}</span>
        </template>
      </el-table-column>
      <el-table-column label="最低报价" min-width="120">
        <template #default="{ row }">
          <span class="price-value">¥{{ Math.min(...row.products.map(p => p.price)).toLocaleString() }}</span>
        </template>
      </el-table-column>
    </el-table>
  </div>
  <div v-else class="no-detail-data" style="padding: 24px; text-align: center; color: #999;">
    暂无供应商数据
  </div>
</el-card>
```

### 3.7 新增样式

在 `<style scoped>` 末尾（约第 1658 行 `</style>` 之前）添加：

```css
.supplier-table {
  margin-top: 8px;
}

.supplier-table .expand-title {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}
```

### 3.8 验证构建

```bash
cd frontend
npm run dev
```
在浏览器中打开 Dashboard，确认：
1. 新卡片出现在"价格分布与关键指标"下方、"详细数据"上方
2. 饼图和柱状图正常渲染
3. 明细表显示供应商数据

- [ ] **Step 7: 提交**

```bash
git add frontend/src/views/Dashboard.vue frontend/src/api/price.js
git commit -m "feat: add supplier comparison card to Dashboard"
```

---

## 自检清单

1. **Spec 覆盖**：饼图、柱状图、明细表三视图全部实现 ✓
2. **占位符扫描**：无 "TBD"、"TODO"、"fill in" 等占位符 ✓
3. **类型一致性**：`supplier`, `product_id`, `price`, `count` 字段名在各任务间一致 ✓
4. **位置确认**：卡片在 Card 2 和 Card 3 之间（Dashboard 第四张卡片）✓

---

## 执行选项

**1. Subagent-Driven (recommended)** - 每个 Task 由独立 subagent 执行，Task 间并行推进

**2. Inline Execution** - 本 session 顺序执行，batch 执行带 checkpoint

哪个方案？