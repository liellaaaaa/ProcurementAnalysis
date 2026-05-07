# ProcurementAnalysis - 采购分析助手

化工原料价格数据采集与可视化系统。

## 功能特性

- **数据采集**: 自动从生意社爬取化工原料价格数据，支持定时更新
- **产品管理**: 支持产品分类管理，灵活的产品筛选
- **价格看板**: 多维度数据可视化（折线图、饼图、柱状图、仪表盘）
- **报表导出**: 支持生成 PDF/Excel 周报、月报
- **预警系统**: 支持阈值、变化率、趋势三种预警类型
- **操作日志**: 完整记录所有关键操作，便于审计追溯

## 技术栈

- **后端**: Python + FastAPI + SQLAlchemy + SQLite
- **前端**: Vue3 + Vite + ECharts + Element Plus
- **爬虫**: Playwright (异步无头浏览器)
- **图表**: ECharts (前端) + matplotlib (后端 PDF)

## 快速启动

### 环境要求

- Python 3.9+
- Node.js 18+
- Playwright 浏览器驱动

### 后端启动

```bash
# 安装依赖
pip install -r requirements.txt

# 安装浏览器
playwright install chromium

# 初始化数据库
python -m backend.models.database

# 启动服务
uvicorn backend.main:app --reload --port 8000
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

### 访问地址

- 前端: http://localhost:5173
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

## 项目结构

```
ProcurementAnalysis/
├── backend/
│   ├── api/routes/       # API 路由
│   ├── scrapers/         # 爬虫模块
│   ├── services/         # 业务服务
│   └── models/           # 数据模型
├── frontend/
│   └── src/
│       ├── views/        # 页面组件
│       ├── components/    # 公共组件
│       └── api/          # API 调用
├── log/                  # 操作日志
└── data/database/        # SQLite 数据库
```

## 主要模块

| 模块 | 说明 |
|------|------|
| 产品管理 | 产品增删改查、分类管理 |
| 价格看板 | 实时数据可视化、多维度分析 |
| 报表中心 | 周报/月报导出（PDF/Excel） |
| 预警管理 | 价格异常告警 |
| 操作日志 | 完整操作审计 |

## 操作日志

系统记录所有关键操作到 `log/operations.log`，包括：
- 产品创建、更新、删除、查询
- 价格数据查询
- 预警配置变更
- 报表生成
- 爬虫执行
- 分类管理

可通过 API 查询：`GET /api/v1/operation-logs`

## 数据来源

- [生意社 (www.100ppi.com)](https://www.100ppi.com) - 化工原料价格数据

## License

MIT
