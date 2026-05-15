# 历史数据爬取方案报告

**日期**: 2026-05-15
**状态**: 待用户确认后执行

---

## 一、问题背景

当前数据库中仅有 61 个产品的最新价格数据（约 2026-05-15），缺少历史价格数据，导致：

1. **涨跌幅全部显示为 0%** - 无法计算环比/同比变化
2. **涨跌排行无数据** - ranking API 返回的 change_percent 全为 0
3. **波动性统计无意义** - avg_volatility 和 max_volatility 都是 0
4. **历史走势图无数据** - Dashboard 折线图无法展示历史趋势

---

## 二、数据源分析

### 2.1 生意社 (www.100ppi.com) 数据结构

根据 `REQUIREMENTS_FROZEN.md`，61 个产品的详情页 URL 格式为：
```
https://www.100ppi.com/rawmex/detail-{id}.html
```

其中包含：
- **当前价格**: 实时现货价格
- **历史价格数据**: 通常提供近几个月到一年的日度价格数据
- **价格走势图**: K 线图形式展示

### 2.2 页面结构分析

生意社详情页通常包含：
1. **当前报价区块**: 今日价格、单位、涨跌额
2. **历史价格表格**: 日期 | 价格 | 涨跌额 | 涨跌% | 趋势
3. **走势图**: 可视化展示

---

## 三、爬取方案

### 3.1 方案一：直接爬取详情页（推荐）

**原理**: 每个产品的详情页已经包含历史价格数据，无需额外接口

**实施步骤**:

1. **遍历 61 个产品详情页**
   - 从已存储的 `products.source_url` 字段获取 URL
   - 使用 Playwright 异步加载页面（绕过 Cloudflare）
   - 解析页面中的历史价格表格

2. **历史数据解析**
   - 找到页面中的历史价格区块（通常在页面中部）
   - 提取字段：日期、价格、涨跌额、涨跌%、趋势
   - 按日期降序存储

3. **增量更新策略**
   - 每次爬取时只抓最新日期的数据
   - 比对数据库中已有数据的最大日期
   - 避免重复插入

### 3.2 方案二：调用生意社历史数据 API

部分生意社页面支持通过 AJAX 请求获取历史数据：

```
POST /rawmex/detail-ajax-{id}.html
Content-Type: application/x-www-form-urlencoded

start_date=2024-01-01&end_date=2026-05-15
```

**优点**: 数据结构化，解析简单
**缺点**: 部分产品可能不支持此接口

---

## 四、技术实现

### 4.1 复用现有爬虫架构

当前 `backend/scrapers/shengyishe.py` 已实现：
- Playwright 浏览器自动化
- Cloudflare 反爬绕过
- 页面解析和数据提取

**修改点**:
1. 新增 `scrape_historical_prices(product_id)` 方法
2. 解析详情页中的历史价格区块
3. 增量写入 `price_records` 表

### 4.2 数据模型对应

```python
# price_records 表关键字段
price_record = {
    "product_id": product.id,           # 产品ID
    "price": 9600.0,                    # 价格数值
    "change_percent": 2.5,              # 涨跌幅 (%)
    "trend": "涨",                      # 趋势
    "record_date": date(2026, 5, 14),  # 日期
    "source": "shengyishe",             # 数据源
}
```

### 4.3 爬取速率控制

- **每产品间隔**: 2-3 秒（避免被封禁）
- **总耗时预估**: 61 产品 × 3 秒 ≈ 3-5 分钟
- **建议时段**: 凌晨 2:00-6:00（低峰期）

---

## 五、实施步骤

### Step 1: 修改爬虫代码
在 `backend/scrapers/shengyishe.py` 中新增方法：

```python
async def scrape_historical_prices(self, product_id: int, days: int = 365) -> List[ScrapedItem]:
    """爬取指定产品的历史价格"""
    # 1. 获取产品信息（URL、名称等）
    # 2. 访问详情页
    # 3. 解析历史价格表格
    # 4. 返回 ScrapedItem 列表
```

### Step 2: 新增批量历史数据爬取 API

```python
@router.post("/scrapers/{source}/scrape-history")
async def scrape_historical_data(source: str, days: int = 365):
    """爬取指定数据源的所有产品历史数据"""
    # 遍历产品列表
    # 调用 scrape_historical_prices
    # 增量写入数据库
```

### Step 3: 执行爬取

```bash
# 通过 API 触发
curl -X POST "http://localhost:8000/api/v1/scrapers/shengyishe/scrape-history" \
     -H "Content-Type: application/json" \
     -d '{"days": 365}'

# 或直接运行脚本
python scripts/scrape_historical_data.py --days 365
```

---

## 六、预期结果

| 指标 | 当前状态 | 爬取后预期 |
|------|----------|------------|
| 历史价格数据 | 0 条 | 约 10,000+ 条 |
| 数据时间范围 | 仅 1 天 | 约 365 天 |
| 涨跌幅数据 | 全为 0 | 正常计算 |
| 涨跌排行 | 无意义 | 正常显示 |

---

## 七、风险与注意事项

1. **反爬机制**: 生意社可能有 Cloudflare 防护，Playwright 已可绕过
2. **数据完整性**: 部分老产品可能只有几个月的数据
3. **增量更新**: 建议每天定时爬取，仅获取新数据
4. **频率限制**: 避免短时间内大量请求

---

## 八、结论

建议采用 **方案一（直接爬取详情页）**，原因：
1. 复用现有 Playwright 架构，改动最小
2. 数据完整性有保障（详情页包含完整历史）
3. 无需寻找隐藏 API，降低依赖风险

**下一步**: 用户确认后开始实施代码改造
