# 供应商智能分析看板 - 设计文档

## 1. 概述

将 Dashboard.vue 中的第四张卡片（供应商对比）从传统列表视图（饼图+柱状图+明细表）升级为**供应商智能分析看板**。

核心特性：
- **Treemap（矩形树状图）**：面积=报价条数(count)，颜色=平均偏离度(avg_deviation)
- **交互式详情面板（20%）**：Hover显示Tooltip，Click展开供应商详情
- **长尾聚合**：前12名独立显示，其余聚合为"更多供应商"(灰色)

## 2. 位置

```
Card 1: 价格分析（折线图 + 涨跌排行）
Card 2: 价格分布与关键指标（饼图 + 指标卡片）
Card 3: 供应商智能分析看板（新，改版）
Card 4: 详细数据（表格）
```

## 3. UI 布局

```
┌─────────────────────────────────────────────────────────────────────────┐
│  供应商智能分析看板                                                      │
├───────────────────────────────────────────┬─────────────────────────────┤
│  产品选择：[下拉（可选）]  时间：[7][30][90] │                             │
├───────────────────────────────────────────┤                             │
│                                           │                             │
│   ┌─────────┬──────────┬───────────────┐  │   ┌─────────────────────┐   │
│   │ 供应商A │  供应商B │    供应商C    │  │   │ 选中供应商详情       │   │
│   │ (大,绿) │ (中,红)  │  (中,绿)      │  │   │                     │   │
│   ├─────────┴──────────┼───────────────┤  │   │ 头部：供应商全称     │   │
│   │   供应商D        │   供应商E      │  │   │ 标签：VIP/战略供应商  │   │
│   │   (中,灰)        │   (小,绿)      │  │   │                     │   │
│   ├──────────────────┴────────────────┤  │   │ 核心指标卡片：        │   │
│   │         更多供应商 (灰色聚合)       │  │   │ - 平均溢价率         │   │
│   └───────────────────────────────────┘  │   │ - 涉及产品数/SKU     │   │
│                                           │   │ - 历史最高/最低报价   │   │
│   Treemap 主屏 (80%)                      │   │                     │   │
│                                           │   │ 可滚动产品清单：      │   │
│                                           │   │ - 产品A | 报价 vs 基准│   │
│                                           │   │ - 产品B | 报价 vs 基准│   │
│                                           │   │                     │   │
│                                           │   └─────────────────────┘   │
│                                           │   详情面板 (20%)            │
└───────────────────────────────────────────┴─────────────────────────────┘
```

## 4. Treemap 渲染规则

### 4.1 数据映射
- **面积（size）**：供应商的 `count`（报价条数）
  - count 越大 → 方块越大
  - 业务含义：活跃度/配合度
- **颜色（color）**：供应商的 `avg_deviation`（平均偏离度）
  - 计算公式：`(avg_price - benchmark_price) / benchmark_price`
  - 业务含义：相对基准价的偏离程度

### 4.2 色阶配置（visualMap pieces）
| 区间 | 颜色 | 业务含义 |
|------|------|---------|
| avg_deviation <= -0.15 | 深绿 `#008000` | 高性价比/优质供应商 |
| -0.15 < avg_deviation < 0.15 | 灰色系（正常波动） | 市场价格正常波动 |
| avg_deviation >= 0.15 | 深红 `#DC143C` | 高价风险/需重点关注 |

**渲染边界（min/max）**：-0.3 到 +0.3（允许显示的极端值）
**分段阈值**：±15%（红绿分水岭）

### 4.3 长尾聚合策略
- **TOP_N_DISPLAY = 12**（可配置，建议10-15）
- 按 count 降序排列，取前 N 名独立展示
- 其余所有供应商聚合为 `id: "others"` 的虚拟节点
  - count = 所有被聚合供应商的 count 之和
  - color = 灰色（表示未分析详情）
  - hover 显示"查看全部 X 个供应商"链接

## 5. 详情面板交互

### 5.1 Hover（悬停）
- 触发：鼠标悬停在 Treemap 任一方块上
- 显示：ECharts Tooltip
  - 供应商名称
  - count（报价条数）
  - avg_deviation（平均偏离度）
  - status_label（如"优"、"风险"）

### 5.2 Click（点击）
- 触发：鼠标点击 Treemap 任一方块
- 行为：右侧 20% 面板刷新内容（选中态）
- 面板内容：
  - **头部**：供应商全称 + 标签（如 VIP、战略供应商）
  - **核心指标卡片**：
    - 平均溢价率：`avg_deviation` 显示绿色/红色
    - 涉及产品数：`product_count`
    - 历史最高报价：`max_price`
    - 历史最低报价：`min_price`
  - **可滚动产品清单**：
    - 每行：产品名称 | 报价 | 基准价 | 偏离度 | 状态标签

### 5.3 空闲态（无选中）
- 面板显示：全局统计摘要（如"共 X 个供应商，平均偏离度 Y%"）
- 或"点击任一方块查看供应商详情"提示

## 6. 后端 API 改造

### 6.1 改造 `/api/v1/prices/supplier-comparison`

**Query 参数**：不变（product_id, days, source, industry）

**返回结构**：扩展为包含 `avg_deviation` 等字段

```json
{
  "supplier_counts": [
    {
      "supplier": "供应商A",
      "count": 36,
      "product_count": 14,
      "avg_price": 90000,
      "avg_deviation": -0.12,
      "max_deviation": 0.05,
      "status_label": "优"
    }
  ],
  "product_supplier_prices": [
    {
      "product_id": 1,
      "product": "AES",
      "supplier": "供应商A",
      "price": 3600,
      "quote_count": 5,
      "benchmark_price": 4000,
      "deviation": -0.10
    }
  ],
  "supplier_products": [
    {
      "supplier": "供应商A",
      "products": [
        {
          "product_id": 1,
          "product": "AES",
          "price": 3600,
          "benchmark_price": 4000,
          "deviation": -0.10,
          "count": 5
        }
      ]
    }
  ]
}
```

### 6.2 计算逻辑

```python
# 对每个供应商的每条报价记录：
deviation = (quote.price - benchmark.price) / benchmark.price

# 供应商综合偏离度 = 加权平均（count 作为权重）
avg_deviation = Σ(deviation_i * count_i) / Σ(count_i)

# 状态标签：
# avg_deviation <= -0.15 → "优"（深绿）
# -0.15 < avg_deviation < 0.15 → "正常"（灰）
# avg_deviation >= 0.15 → "风险"（深红）
```

## 7. 前端组件结构

### 7.1 Treemap 组件
- 使用 ECharts `treemap` 类型
- `visualMap` 配置色阶 pieces
- `tooltip` formatter 显示摘要
- `click` 事件触发详情面板更新

### 7.2 详情面板组件
- 右侧固定 20% 宽度
- 空闲态：显示统计摘要
- 选中态：显示供应商详情 + 产品列表
- 可滚动（max-height + overflow-y: auto）

## 8. 实现步骤

1. **后端**：改造 `/api/v1/prices/supplier-comparison`，增加 `avg_deviation`、`max_deviation`、`status_label`、`benchmark_price`、`deviation` 字段
2. **前端 API**：确认 `price.js` 的 `getSupplierComparison` 方法能接收新字段
3. **前端**：重构 Dashboard.vue 供应商卡片
   - 移除旧饼图+柱状图+明细表
   - 新增 Treemap（80%）+ 详情面板（20%）
   - 实现 visualMap 色阶配置
   - 实现长尾聚合（前12名 + others）
   - 实现 hover tooltip 和 click 详情面板交互
4. **测试**：验证 Treemap 渲染、色阶映射、详情面板交互

## 9. 关键技术细节

### 9.1 ECharts Treemap 配置
```javascript
{
  series: [{
    type: 'treemap',
    data: treemapData,  // 已处理好的节点数据
    visualMin: -0.3,
    visualMax: 0.3,
    visualMap: {
      show: false,
      pieces: [
        { lte: -0.15, color: '#008000' },
        { gt: -0.15, lte: 0.15, color: '#D3D3D3' },
        { gt: 0.15, color: '#DC143C' }
      ]
    },
    label: { show: true, formatter: '{b}' },
    tooltip: {
      formatter: (params) => `${params.name}<br/>报价: ${params.data.count}条<br/>偏离: ${(params.data.avg_deviation * 100).toFixed(1)}%`
    }
  }]
}
```

### 9.2 长尾聚合伪代码
```javascript
function processSuppliers(suppliers, topN = 12) {
  const sorted = [...suppliers].sort((a, b) => b.count - a.count)
  const top = sorted.slice(0, topN)
  const others = sorted.slice(topN)

  const nodes = top.map(s => ({
    name: s.supplier,
    value: s.count,
    avg_deviation: s.avg_deviation,
    status_label: s.status_label
  }))

  if (others.length > 0) {
    nodes.push({
      name: `其他供应商 (${others.length}家)`,
      value: others.reduce((sum, s) => sum + s.count, 0),
      avg_deviation: null,  // 灰色
      status_label: '未分析'
    })
  }

  return nodes
}
```