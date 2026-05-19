# 部署指南 for Windows 服务器

## 环境要求

- Windows Server 2019/2022 或 Windows 11
- Python 3.10+
- Node.js 18+

---

## 第一步：服务器环境准备

### 1.1 安装 Python（如果尚未安装）

1. 下载 Python 3.10+: https://www.python.org/downloads/
2. 安装时勾选 "Add Python to PATH"
3. 验证：`python --version`

### 1.2 安装 Node.js（如果尚未安装）

1. 下载 Node.js 18+: https://nodejs.org/
2. 验证：`node --version` 和 `npm --version`

---

## 第二步：上传项目文件

将整个 `ProcurementAnalysis` 文件夹上传到服务器，建议路径：

```
C:\ProcurementAnalysis\
```

---

## 第三步：安装后端依赖

打开命令提示符（管理员）：

```bash
cd C:\ProcurementAnalysis

# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器（重要！）
playwright install chromium

# 初始化数据库
python -m backend.models.database
```

---

## 第四步：构建前端

```bash
cd C:\ProcurementAnalysis\frontend
npm install
npm run build
```

构建完成后会生成 `C:\ProcurementAnalysis\frontend\dist\` 目录。

---

## 第五步：启动服务

### 方式一：手动启动

```bash
cd C:\ProcurementAnalysis
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 方式二：一键启动（推荐）

双击运行 `C:\ProcurementAnalysis\start.bat`

---

## 第六步：防火墙配置

### 开放端口

使用命令（管理员）：

```bash
netsh advfirewall firewall add rule name="ProcurementAnalysis" dir=in action=allow protocol=tcp localport=8000
```

---

## 验证部署

启动服务后，在浏览器中访问：

- 前端页面：`http://服务器公网IP:8000/`
- API 文档：`http://服务器公网IP:8000/docs`
- 健康检查：`http://服务器公网IP:8000/health`

---

## 配置开机自启

### 使用任务计划程序

1. 打开"任务计划程序"（taskschd.msc）
2. 点击"创建基本任务..."
3. 名称：`ProcurementAnalysis 自动启动`
4. 触发器：选择"计算机启动时"
5. 操作：选择"启动程序"
6. 程序/脚本：`C:\ProcurementAnalysis\start.bat`
7. 完成

---

## 公网访问（无域名方案）

如果服务器没有公网 IP 或在防火墙内，可以使用内网穿透工具：

### ngrok（推荐）

1. 下载 ngrok：https://ngrok.com/download
2. 注册账号获取 authtoken
3. 运行：`ngrok http 8000`
4. 会获得一个公网地址如 `https://xxxx.ngrok.io`

### 微软 tunneling（免费额度）

```bash
npx localtunnel --port 8000
```

---

## 目录结构

部署完成后应该是这样的结构：

```
C:\ProcurementAnalysis\
├── backend\           # 后端代码
├── data\              # 数据库目录
├── frontend\
│   ├── dist\          # 前端构建产物（npm run build 后生成）
│   └── src\           # 前端源码
├── log\               # 日志目录
├── start.bat          # 一键启动脚本
└── requirements.txt   # Python 依赖
```

---

## 常见问题

### Q: 访问显示 404

检查 dist 目录是否存在：`dir C:\ProcurementAnalysis\frontend\dist\`

### Q: 页面空白或样式丢失

可能是路径问题，检查 backend/main.py 中的路径是否正确

### Q: 需要重启服务

按 Ctrl+C 停止，然后重新运行 start.bat