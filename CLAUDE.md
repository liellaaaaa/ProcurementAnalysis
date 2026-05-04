# ProcurementAnalysis - 采购分析助手

化工原料价格数据采集与可视化系统。

## 技术栈

- **后端**: Python + FastAPI + SQLAlchemy + SQLite
- **前端**: Vue3 + Vite + ECharts + Element Plus
- **爬虫**: Playwright (异步无头浏览器，绕过 Cloudflare 反爬)
- **数据源**: 生意社 (www.100ppi.com)

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
│   ├── prices.py        # 价格 API
│   └── scrapers.py      # 爬虫管理 API
└── models/              # 数据模型
    └── database.py      # 数据库模型

frontend/
├── src/
│   ├── views/           # 页面
│   │   ├── Dashboard.vue
│   │   └── ProductCompare.vue
│   ├── components/      # 组件
│   │   └── SourceSelector.vue  # 数据源选择器
│   ├── api/             # API 调用
│   └── router/          # 路由配置
└── package.json
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

## API 端点

### 产品管理
- `GET /api/v1/products` - 产品列表
- `GET /api/v1/products/{product_id}` - 产品详情
- `POST /api/v1/products` - 创建产品
- `DELETE /api/v1/products/{product_id}` - 删除产品

### 价格数据
- `GET /api/v1/prices` - 价格列表（支持 source, product_id, date 过滤）
- `GET /api/v1/prices/latest` - 各产品最新价格
- `GET /api/v1/prices/history/{product_id}` - 产品历史价格趋势
- `GET /api/v1/prices/stats/summary` - 统计摘要

### 爬虫管理
- `GET /api/v1/sources` - 已注册的数据源列表
- `POST /api/v1/scrapers/{source}/run` - 触发指定数据源爬取

## 数据模型

- `products` - 产品目录（含 source 字段标识数据来源）
- `price_records` - 价格历史（含 source 字段）
- `alert_configs` - 预警配置（待实现）
- `scraper_logs` - 爬虫运行日志

## 数据源扩展

新增数据源只需：
1. 在 `backend/scrapers/` 下创建新的爬虫类，继承 `BaseScraper`
2. 在 `scrapers/__init__.py` 中注册到 `ScraperRegistry`
3. 前端数据源下拉框从 `/api/v1/sources` 动态获取，无需硬编码