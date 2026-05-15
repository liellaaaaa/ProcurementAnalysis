# 采购分析系统 - 数据源与产品管理改造计划

## 需求冻结版 v1.0

> **冻结日期**: 2026-05-14
> **状态**: 已冻结，等待开发
> **后续更动需记录至 CHANGELOG**

---

## 一、数据源架构（工厂模式）

### 架构设计
```
BaseScraper (抽象基类)
    │
    ├── ShengyisheScraper (生意社)
    │     ├── 化工: https://www.100ppi.com/rawmex/detail-{id}.html (54个品类)
    │     ├── 能源: 3个详情页（液化天然气/Brent原油/WTI原油）
    │     ├── 农副: 2个详情页（玉米/棕榈油）
    │     └── 有色: 2个详情页（黄金/金属硅）
    │
    └── [未来扩展] 其他数据源
```

---

## 二、采购部品类清单（共61个）

### 2.1 化工（54个品类）- 详情页

| 序号 | 品类名称 | URL |
|------|---------|-----|
| 1 | AES | https://www.100ppi.com/rawmex/detail-1544.html |
| 2 | DMF | https://www.100ppi.com/rawmex/detail-786.html |
| 3 | EGDA | https://www.100ppi.com/rawmex/detail-1611.html |
| 4 | TDI | https://www.100ppi.com/rawmex/detail-1095.html |
| 5 | 苯酚 | https://www.100ppi.com/rawmex/detail-464.html |
| 6 | 丙二醇甲醚醋酸酯 | https://www.100ppi.com/rawmex/detail-1482.html |
| 7 | 丙酮 | https://www.100ppi.com/rawmex/detail-582.html |
| 8 | 丙烯 | https://www.100ppi.com/rawmex/detail-505.html |
| 9 | 丙烯酸 | https://www.100ppi.com/rawmex/detail-584.html |
| 10 | 丙烯酰胺 | https://www.100ppi.com/rawmex/detail-1615.html |
| 11 | 纯苯 | https://www.100ppi.com/rawmex/detail-120.html |
| 12 | 醋酸 | https://www.100ppi.com/rawmex/detail-218.html |
| 13 | 电石 | https://www.100ppi.com/rawmex/detail-640.html |
| 14 | 丁酮肟 | https://www.100ppi.com/rawmex/detail-1703.html |
| 15 | 二丙二醇 | https://www.100ppi.com/rawmex/detail-1519.html |
| 16 | 二甘醇 | https://www.100ppi.com/rawmex/detail-1332.html |
| 17 | 二甲胺水溶液 | https://www.100ppi.com/rawmex/detail-1555.html |
| 18 | 二乙醇胺 | https://www.100ppi.com/rawmex/detail-1483.html |
| 19 | 富马酸 | https://www.100ppi.com/rawmex/detail-1593.html |
| 20 | 过硫酸铵 | https://www.100ppi.com/rawmex/detail-1474.html |
| 21 | 过硫酸钾 | https://www.100ppi.com/rawmex/detail-1508.html |
| 22 | 过硫酸钠 | https://www.100ppi.com/rawmex/detail-1486.html |
| 23 | 环氧丙烷 | https://www.100ppi.com/rawmex/detail-438.html |
| 24 | 环氧氯丙烷 | https://www.100ppi.com/rawmex/detail-439.html |
| 25 | 环氧树脂 | https://www.100ppi.com/rawmex/detail-1304.html |
| 26 | 环氧乙烷 | https://www.100ppi.com/rawmex/detail-856.html |
| 27 | 黄磷 | https://www.100ppi.com/rawmex/detail-708.html |
| 28 | 甲醇 | https://www.100ppi.com/rawmex/detail-817.html |
| 29 | 甲醛 | https://www.100ppi.com/rawmex/detail-778.html |
| 30 | 焦亚硫酸钠 | https://www.100ppi.com/rawmex/detail-648.html |
| 31 | 聚丙烯酰胺 | https://www.100ppi.com/rawmex/detail-1283.html |
| 32 | 聚合MDI | https://www.100ppi.com/rawmex/detail-975.html |
| 33 | 磷酸 | https://www.100ppi.com/rawmex/detail-709.html |
| 34 | 硫磺 | https://www.100ppi.com/rawmex/detail-427.html |
| 35 | 硫脲 | https://www.100ppi.com/rawmex/detail-1497.html |
| 36 | 硫酸 | https://www.100ppi.com/rawmex/detail-236.html |
| 37 | 硫酸二甲酯 | https://www.100ppi.com/rawmex/detail-1693.html |
| 38 | 硫酸二乙酯 | https://www.100ppi.com/rawmex/detail-1668.html |
| 39 | 尿素 | https://www.100ppi.com/rawmex/detail-89.html |
| 40 | 轻质纯碱 | https://www.100ppi.com/rawmex/detail-226.html |
| 41 | 三乙醇胺 | https://www.100ppi.com/rawmex/detail-1470.html |
| 42 | 双氰胺 | https://www.100ppi.com/rawmex/detail-1727.html |
| 43 | 双氧水 | https://www.100ppi.com/rawmex/detail-758.html |
| 44 | 顺酐 | https://www.100ppi.com/rawmex/detail-660.html |
| 45 | 盐酸 | https://www.100ppi.com/rawmex/detail-355.html |
| 46 | 一水柠檬酸 | https://www.100ppi.com/rawmex/detail-1471.html |
| 47 | 衣康酸 | https://www.100ppi.com/rawmex/detail-1591.html |
| 48 | 乙二醇丁醚 | https://www.100ppi.com/rawmex/detail-1465.html |
| 49 | 异丙醇 | https://www.100ppi.com/rawmex/detail-941.html |
| 50 | 异辛醇 | https://www.100ppi.com/rawmex/detail-489.html |
| 51 | 油酸 | https://www.100ppi.com/rawmex/detail-1558.html |
| 52 | 有机硅DMC | https://www.100ppi.com/rawmex/detail-751.html |
| 53 | 元明粉 | https://www.100ppi.com/rawmex/detail-1504.html |
| 54 | 精萘 | https://www.100ppi.com/rawmex/detail-1655.html |

---

### 2.2 能源（3个品类）- 详情页

| 品类 | URL |
|------|-----|
| 液化天然气 | https://www.100ppi.com/rawmex/detail-897.html |
| Brent原油 | https://www.100ppi.com/rawmex/detail-1127.html |
| WTI原油 | https://www.100ppi.com/rawmex/detail-1036.html |

---

### 2.3 农副（2个品类）- 详情页

| 品类 | URL |
|------|-----|
| 玉米 | https://www.100ppi.com/rawmex/detail-274.html |
| 棕榈油 | https://www.100ppi.com/rawmex/detail-820.html |

---

### 2.4 有色（2个品类）- 详情页

| 品类 | URL |
|------|-----|
| 黄金 | https://www.100ppi.com/rawmex/detail-551.html |
| 金属硅 | https://www.100ppi.com/rawmex/detail-238.html |

---

## 三、数据库设计

### 产品表 (products)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| product_name | String | 产品名称 |
| industry | String | 行业（化工/能源/农副/有色） |
| category | String | 品类（二级分类） |
| unit | String | 默认单位（元/吨、元/克、元/立方米） |
| source | String | 数据源 |
| source_url | String | 来源URL |
| is_active | Boolean | 是否有效（软删除） |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

---

### 价格记录表 (price_records) - 完整字段

| 字段 | 类型 | 说明 | 备注 |
|------|------|------|------|
| id | Integer | 主键 | |
| product_id | Integer | 关联产品（FK） | |
| price | Decimal | 价格数值 | 用于计算统计 |
| unit | String | 单位 | 元/吨、元/克、元/立方米 |
| price_original | String | 原始报价 | 如"2750元/吨"、"1025.99元/克" |
| price_category | String | 价格类别 | 现货/期货 |
| region | String | 交货地 | 省/市，如"山东省/济南市" |
| supplier | String | 交易商/供应商 | |
| record_date | Date | 发布/交易日期 | |
| source | String | 数据源 | shengyishe |
| extra_data | JSON | 行业差异化字段 | 见下方详解 |
| created_at | DateTime | 创建时间 | |

---

### extra_data 扩展字段（按行业）

#### 化工（详情页格式）

| 字段 | 示例 |
|------|------|
| 规格 | "含量99.9%" |
| 品牌/产地 | "国产"、"兖矿" |
| 报价类型 | "市场价" |

```json
{"规格": "含量99.9%", "品牌/产地": "国产", "报价类型": "市场价"}
```

---

#### 能源（详情页格式）

| 字段 | 示例 |
|------|------|
| 规格 | "300kg/桶" |
| 数量 | "30吨" |
| 现货类型 | "即期现货"、"合约现货" |
| 有效时间 | "7天" |

```json
{"规格": "300kg/桶", "数量": "30吨", "现货类型": "即期现货", "有效时间": "7天"}
```

---

#### 农副（详情页格式）

| 字段 | 示例 |
|------|------|
| 分类 | "食用精炼棕榈液油"（棕榈油）、"黄玉米"（玉米） |
| 等级/熔点等 | "等级:3"、"熔点(℃):24" |
| 品牌/产地 | "进口"、"吉林长春" |
| 报价类型 | "市场价" |

```json
{"分类": "食用精炼棕榈液油", "熔点(℃)": "24", "品牌/产地": "进口", "报价类型": "市场价"}
```

---

#### 有色（详情页格式）

| 字段 | 示例 |
|------|------|
| 品名/纯度 | "Au不小于(%):99.99"（黄金）、"441#"（金属硅） |
| 品牌/产地 | "上海"、"黄埔港" |
| 报价类型 | "市场价" |

```json
{"品名": "441#", "硅(Si)含量(%)≥": "99", "品牌/产地": "黄埔港", "报价类型": "市场价"}
```

---

## 四、实施步骤

### Step 1: 数据库改造
- 修改 `backend/models/database.py`
- products 表添加 `industry` 字段
- price_records 表添加 `unit`, `price_original`, `price_category`, `extra_data` 字段

### Step 2: 爬虫工厂模式重构
- 修改 `backend/scrapers/registry.py` - 实现工厂注册
- 修改 `backend/scrapers/shengyishe.py` - 支持多行业URL pattern（61个详情页）
- 重构 `save_to_db` 方法支持 extra_data JSON字段

### Step 3: 批量导入API
- 新增 `POST /api/v1/products/batch` - 批量导入61个产品
- 支持按产品名称匹配，跳过已存在产品
- 导入时指定行业属性

### Step 4: 前端改造
- `SourceSelector.vue` → 数据源选择器（当前仅生意社）
- `CategorySelector.vue` → 行业联动筛选
- `Dashboard.vue` → 按行业筛选
- `ProductManage.vue` → 显示行业属性
- `ProductCompare.vue` → 按行业筛选

### Step 5: 数据清理与导入
- 软删除现有2219个产品
- 批量导入61个产品

---

## 五、关键文件清单

| 文件 | 修改内容 |
|------|---------|
| `backend/models/database.py` | 添加industry/unit/price_original/price_category/extra_data字段 |
| `backend/scrapers/registry.py` | 工厂模式注册中心 |
| `backend/scrapers/shengyishe.py` | 多行业URL支持、extra_data保存 |
| `backend/api/routes/products.py` | 批量导入API、行业筛选 |
| `backend/api/routes/scrapers.py` | 数据源管理API |
| `frontend/src/components/SourceSelector.vue` | 数据源选择器 |
| `frontend/src/components/CategorySelector.vue` | 行业联动 |
| `frontend/src/views/Dashboard.vue` | 按行业筛选 |
| `frontend/src/views/ProductManage.vue` | 行业属性显示 |
| `frontend/src/views/ProductCompare.vue` | 行业筛选联动 |

---

## 六、验证方式

1. 爬取测试：化工/能源/农副/有色各选一个品类验证数据
2. 批量导入：调用API导入61个产品
3. 前端验证：按行业筛选、数据看板展示

---

## CHANGELOG（更动记录）

| 日期 | 更动内容 | 负责人 |
|------|---------|--------|
| 2026-05-14 | 需求冻结 v1.0 | - |
| 2026-05-14 | 更新：化工54个品类URL全部匹配成功 | - |
| 2026-05-14 | 更新：所有品类确认使用详情页(rawmex/detail-{id}.html) | - |