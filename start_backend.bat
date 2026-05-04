@echo off
REM ProcurementAnalysis 启动脚本

echo [1/3] 激活虚拟环境...
call venv\Scripts\activate.bat

echo [2/3] 初始化数据库（如果需要）...
python -m backend.models.database

echo [3/3] 启动后端服务...
start "ProcurementAnalysis API" cmd /k "uvicorn backend.main:app --reload --port 8000"

echo.
echo 后端服务已启动: http://localhost:8000
echo API 文档: http://localhost:8000/docs
echo.
echo 前端启动: cd frontend ^&^& npm run dev
pause