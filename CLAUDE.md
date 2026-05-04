# ProcurementAnalysis - 采购分析助手

化工原料价格数据采集与可视化系统。

## 技术栈

- **后端**: Python + FastAPI + SQLAlchemy + SQLite
- **前端**: Vue3 + Vite + ECharts + Element Plus
- **数据源**: 生意社 (www.100ppi.com)

## 项目结构

```
backend/
├── main.py              # FastAPI 入口
├── config.py            # 配置
├── scrapers/            # 爬虫模块
│   ├── base.py          # 爬虫基类
│   └── shengyishe.py    # 生意社爬虫
├── api/routes/          # API 路由
│   ├── products.py      # 产品 API
│   └── prices.py        # 价格 API
└── models/              # 数据模型
    └── database.py      # 数据库模型

frontend/
├── src/
│   ├── views/           # 页面
│   │   ├── Dashboard.vue
│   │   └── ProductCompare.vue
│   ├── api/              # API 调用
│   └── router/          # 路由配置
└── package.json
```

## 启动方式

### 后端
```bash
cd backend
pip install -r requirements.txt
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

- `GET /api/v1/products` - 产品列表
- `GET /api/v1/prices/latest` - 最新价格
- `GET /api/v1/prices/history/{product_id}` - 历史价格
- `GET /api/v1/prices/stats/summary` - 统计摘要

## 数据模型

- `products` - 产品目录
- `price_records` - 价格历史
- `alert_configs` - 预警配置
- `scraper_logs` - 爬虫日志