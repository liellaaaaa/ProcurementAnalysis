# 统一时间筛选组件 `<PeriodSelector>` 设计方案

## 1. 背景与问题

现有时间筛选逻辑分散在 Dashboard、ProductCompare、ReportView 三个视图，各自有独立的状态变量和 UI 实现，存在以下问题：

- **Dashboard 卡片1**：`filter1DateRange`（date-picker）和 `compareDays`（el-select）互斥并存，逻辑混乱
- **Dashboard 卡片2**：`filter2DateRange` 绑了 v-model 但 API 从不看，直接 hardcode `days: 30`
- **Dashboard 卡片3**：`supplierComparisonDays` 独立控制，与其他卡片无关
- **ProductCompare**：`selectedDays` + `dateRange` 部分互斥，但 `showCustomDate` 切换逻辑不完整
- **ReportView**：`month` / `startDate` / `endDate` 相对清晰但未复用

核心矛盾：每个视图/卡片各自为政，没有统一的语义和组件。

## 2. 设计原则

- **业务无关** — 组件只知道"选日期"，不知道什么价格、供应商、报表
- **格式无关** — 组件 emit `start_date/end_date`（`YYYY-MM-DD`），不关心 SQL 怎么查
- **单一职责** — 组件管 UI + 互斥逻辑，父组件管请求参数拼接

## 3. 组件接口

### 使用方式

```vue
<PeriodSelector 
  v-model:startDate="startDate" 
  v-model:endDate="endDate" 
/>
```

### Props

| Prop | 类型 | 必填 | 说明 |
|------|------|------|------|
| `startDate` | String | 否 | 外部初始起始日期 `YYYY-MM-DD`，不传则用默认值 7d |
| `endDate` | String | 否 | 外部初始结束日期 `YYYY-MM-DD`，不传则用默认值今天 |

### Emits

| Event | Payload | 说明 |
|-------|---------|------|
| `update:startDate` | `String \| null` | 更新后的起始日期，`all` 模式下为 `null` |
| `update:endDate` | `String \| null` | 更新后的结束日期，`all` 模式下为 `null` |

### 组件内部状态

```
period: '1d' | '7d' | '30d' | '90d' | 'all' | 'custom'
```

- `period` 不暴露给父组件，仅内部互斥逻辑使用
- `'custom'` 时显示 el-date-picker，其余值隐藏 picker
- `'all'` 时 `start = null, end = null`（后端查全部历史）

## 4. 快捷按钮

```
[1天] [7天] [30天] [90天] [全部] [自定义 ▼]
```

### 日期计算规则

| period | start | end |
|--------|-------|-----|
| `1d` | 今天 | 今天 |
| `7d` | 今天 - 6 | 今天 |
| `30d` | 今天 - 29 | 今天 |
| `90d` | 今天 - 89 | 今天 |
| `all` | null | null |
| `custom` | 用户选择 | 用户选择 |

### 互斥逻辑

- 点击任意快捷按钮 → `period = 该值`，隐藏 picker，清空 `startDate/endDate` 为计算值
- 点击「自定义」 → `period = 'custom'`，显示 picker
- 切换快捷按钮时**不清空 picker 内容**，下次点自定义仍保留上次选择
- picker change 时自动设置 `period = 'custom'`

## 5. 日期格式

- **组件 emit 格式**：`YYYY-MM-DD`（与后端 SQL 格式一致）
- **组件内部计算**：使用 `toISOString().split('T')[0]` 或 dayjs
- **el-date-picker 格式**：`value-format="YYYY-MM-DD"`

## 6. 各视图接入方式

### Dashboard 卡片1（价格走势 + 涨跌排行）

```vue
<PeriodSelector 
  v-model:startDate="filter1Start" 
  v-model:endDate="filter1End" 
/>
```

- `loadFilter1Charts()` 监听 `filter1Start/filter1End` 变化
- 内部将日期范围换算为 `days` 传给 `getBenchmarkHistoryMulti` 和 `getDashboardRanking`

### Dashboard 卡片2（价格分布饼图）

```vue
<PeriodSelector 
  v-model:startDate="filter2Start" 
  v-model:endDate="filter2End" 
/>
```

- `loadDistributionData()` 监听变化
- 内部将日期换算为 `days` 传给 `getDashboardDistribution`

### Dashboard 卡片3（供应商看板）

```vue
<PeriodSelector 
  v-model:startDate="supplierStart" 
  v-model:endDate="supplierEnd" 
/>
```

- `loadSupplierComparison()` 监听变化
- 内部将日期换算为 `days` 传给 `getSupplierComparison`

### ProductCompare

```vue
<PeriodSelector 
  v-model:startDate="compareStart" 
  v-model:endDate="compareEnd" 
/>
```

- `loadComparison()` 监听变化，直接用 start/end 传给 `getBenchmarkHistoryMulti`

### ReportView（周报模式）

```vue
<PeriodSelector 
  v-model:startDate="reportStart" 
  v-model:endDate="reportEnd" 
/>
```

- 月报模式（`reportType === 'monthly'`）不启用 PeriodSelector，直接传 `month`
- 周报模式启用 PeriodSelector，emit 的日期传给 `getPrices` 和报表下载接口

## 7. 后端接口（无需改动）

后端已有 `start_date` + `end_date` Query 参数，前端直接传入 `YYYY-MM-DD` 字符串即可。

## 8. 需要删除的废弃代码

### Dashboard.vue

- `filter1DateRange`（第464行，el-date-picker）
- `filter2DateRange`（第472行，el-date-picker）
- `compareDays`（第490行，el-select 7/30/90）
- `supplierComparisonDays`（第501行）
- `expandChartDays`（第491行，未使用）
- `watch(filter1DateRange, ...)` 相关代码（不存在，但需检查）
- `watch(filter2DateRange, ...)` 相关代码（不存在，但需检查）

### ProductCompare.vue

- `datePresets` 数组（第126行）
- `selectedDays`（第127行）
- `showCustomDate`（第128行）
- `setDateDays()` 函数（第163-168行）
- `dateRange` 相关的旧逻辑（第125行，第196-199行）

### ReportView.vue

- 无需删除，继续使用 PeriodSelector 替换 `startDate/endDate` 的 el-date-picker

## 9. 组件文件位置

```
frontend/src/components/PeriodSelector.vue
```

## 10. 实现检查清单

- [ ] 创建 `PeriodSelector.vue` 组件
- [ ] 实现快捷按钮 1d/7d/30d/90d/all/custom
- [ ] 实现自定义 picker 默认隐藏、按钮切换显示
- [ ] 实现互斥逻辑
- [ ] 实现日期计算（今天 - N 天）
- [ ] 实现 emit `update:startDate` 和 `update:endDate`
- [ ] Dashboard.vue 接入卡片1
- [ ] Dashboard.vue 接入卡片2
- [ ] Dashboard.vue 接入卡片3
- [ ] ProductCompare.vue 替换旧时间筛选
- [ ] ReportView.vue 周报模式接入
- [ ] 删除 Dashboard.vue 废弃变量和代码
- [ ] 删除 ProductCompare.vue 废弃变量和代码
- [ ] 验证各视图时间筛选独立工作
