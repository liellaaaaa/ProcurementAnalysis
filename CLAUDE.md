# ProcurementAnalysis - 采购分析助手

化工原料价格数据采集与可视化系统。

## 技术栈

- **后端**: Python + FastAPI + SQLAlchemy + SQLite
- **前端**: Vue3 + Vite + ECharts + Element Plus
- **爬虫**: Playwright (异步无头浏览器，绕过 Cloudflare 反爬)
- **数据源**: 生意社 (www.100ppi.com)
- **图表**: ECharts (前端) + matplotlib (后端 PDF 图表生成)

## 项目结构

```
backend/
├── main.py              # FastAPI 入口
├── config.py            # 配置
├── scrapers/            # 爬虫模块
│   ├── base.py          # 爬虫基类
│   ├── registry.py      # 爬虫注册中心
│   └── shengyishe.py    # 生意社爬虫
├── api/routes/          # API 路由
│   ├── products.py      # 产品 API
│   ├── prices.py        # 价格 API (含 Dashboard API)
│   ├── scrapers.py      # 爬虫管理 API
│   ├── analytics.py     # 分析 API (预测、排行)
│   ├── reports.py       # 报表生成 API (PDF/Excel)
│   ├── alerts.py        # 预警 API
│   ├── categories.py     # 分类管理 API
│   └── operation_logs.py # 操作日志 API
├── services/            # 业务服务
│   ├── alert_service.py     # 预警服务
│   ├── chart_generator.py   # matplotlib 图表生成服务
│   └── operation_logger.py  # 操作日志服务
└── models/              # 数据模型
    └── database.py      # 数据库模型

frontend/
├── src/
│   ├── views/           # 页面
│   │   ├── Dashboard.vue       # 数据看板
│   │   ├── ProductCompare.vue  # 产品对比
│   │   ├── ProductManage.vue   # 产品管理
│   │   ├── CategoryManage.vue  # 分类管理
│   │   ├── ReportView.vue      # 报表中心
│   │   └── AlertView.vue       # 预警管理
│   ├── components/      # 组件
│   │   ├── SourceSelector.vue   # 数据源选择器
│   │   └── CategorySelector.vue # 分类选择器
│   ├── api/             # API 调用
│   └── router/          # 路由配置
└── package.json

log/                     # 操作日志目录
└── operations.log       # 操作日志文件
```

## 启动方式

### 后端
```bash
cd C:\Users\windows\Desktop\ProcurementAnalysis
pip install -r requirements.txt
playwright install chromium  # 安装浏览器
python -m backend.models.database  # 初始化数据库
uvicorn backend.main:app --reload --port 8000
```

### 前端
```bash
cd frontend
npm install
npm run dev
```

## 依赖说明

### Python 依赖 (requirements.txt)
- **核心**: fastapi, uvicorn, sqlalchemy, aiosqlite
- **爬虫**: playwright, beautifulsoup4, lxml
- **图表**: matplotlib, numpy, openpyxl
- **其他**: loguru, pydantic, python-dateutil, schedule

**注意**: 所有日期格式统一使用 `yyyy/mm/dd`

### 前端依赖 (package.json)
- **框架**: vue, vite
- **UI**: element-plus
- **图表**: echarts

## API 端点

### 产品管理
- `GET /api/v1/products` - 产品列表（支持品类筛选）
- `GET /api/v1/products/{product_id}` - 产品详情
- `POST /api/v1/products` - 创建产品
- `PUT /api/v1/products/{product_id}` - 更新产品
- `DELETE /api/v1/products/{product_id}` - 删除产品（软删除）

### 价格数据
- `GET /api/v1/prices` - 价格列表（支持 source, product_id, date 过滤）
- `GET /api/v1/prices/latest` - 各产品最新价格（分页+筛选）
- `GET /api/v1/prices/history/{product_id}` - 产品历史价格趋势
- `GET /api/v1/prices/stats/summary` - 统计摘要

### Dashboard API (价格看板)
- `GET /api/v1/prices/dashboard/distribution` - 价格占比（饼图数据）
- `GET /api/v1/prices/dashboard/ranking` - 涨跌排行（柱状图数据）
- `GET /api/v1/prices/dashboard/history/compare` - 多产品走势对比（折线图数据）
- `GET /api/v1/prices/dashboard/volatility` - 价格波动统计（仪表盘数据）

### 报表生成
- `GET /api/v1/reports/pdf?report_type=weekly|monthly` - 生成 PDF 报表（含图表）
- `GET /api/v1/reports/excel?report_type=weekly|monthly` - 生成 Excel 报表（含图表）

### 预警管理
- `GET /api/v1/alerts/configs` - 预警配置列表
- `POST /api/v1/alerts/configs` - 创建预警配置
- `PUT /api/v1/alerts/configs/{id}` - 更新预警配置
- `DELETE /api/v1/alerts/configs/{id}` - 删除预警配置
- `GET /api/v1/alerts` - 预警记录列表
- `PUT /api/v1/alerts/{id}/read` - 标记已读
- `PUT /api/v1/alerts/read-all` - 全部已读
- `DELETE /api/v1/alerts/{id}` - 删除预警记录

### 分类管理
- `GET /api/v1/categories` - 所有分类（树形结构）
- `GET /api/v1/categories/level-one` - 一级分类
- `GET /api/v1/categories/level-two/{parent_id}` - 二级分类
- `POST /api/v1/categories` - 创建分类
- `PUT /api/v1/categories/{id}` - 更新分类
- `DELETE /api/v1/categories/{id}` - 删除分类

### 操作日志
- `GET /api/v1/operation-logs` - 查询操作日志（支持 keyword/module/level/date 过滤）
- `GET /api/v1/operation-logs/modules` - 获取模块列表
- `GET /api/v1/operation-logs/summary` - 日志统计摘要

### 数据新鲜度检测
- `GET /api/v1/check-freshness` - 检查数据是否过期

### 爬虫管理
- `GET /api/v1/sources` - 已注册的数据源列表
- `POST /api/v1/scrapers/{source}/run` - 触发指定数据源爬取

## 数据模型

- `products` - 产品目录（含 source, category, unit 字段）
- `price_records` - 价格历史（含 source, region, supplier, brand, specification 字段）
- `alert_configs` - 预警配置（支持 threshold/change_rate/trend 三种类型）
- `alert_records` - 预警记录
- `scraper_logs` - 爬虫运行日志
- `categories` - 产品分类（支持二级分类）
- `product_categories` - 产品-分类关联表
- `operation_logs` - 操作日志

## 操作日志

所有关键操作都会记录到 `log/operations.log`，包括：
- 产品增删改查
- 价格查询
- 预警配置操作
- 报表生成
- 爬虫运行
- 分类管理

日志格式为 JSON，便于后续分析。

## 数据源扩展

新增数据源只需：
1. 在 `backend/scrapers/` 下创建新的爬虫类，继承 `BaseScraper`
2. 在 `scrapers/__init__.py` 中注册到 `ScraperRegistry`
3. 前端数据源下拉框从 `/api/v1/sources` 动态获取，无需硬编码

## 仪表台功能

Dashboard.vue 提供以下图表：
- **折线图**: 多产品价格走势对比（支持 7/30/90 天切换）
- **饼图**: 各产品价格记录占比
- **柱状图**: 涨跌排行 TOP10
- **仪表盘**: 价格平均波动幅度监控

## 报表功能

支持导出周报/月报：
- **PDF**: 包含涨跌排行柱状图、价格占比饼图、产品明细表
- **Excel**: 包含产品列表、价格历史、统计汇总、涨跌排行图表、价格占比图表
