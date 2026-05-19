@echo off
REM ProcurementAnalysis 一键启动脚本

echo ========================================
echo 采购分析系统启动中...
echo ========================================

cd /d "%~dp0"

echo [1/3] 启动后端服务 (端口 8000)...
start "ProcurementAnalysis API" cmd /k "cd /d %~dp0 && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"

echo.
echo ========================================
echo 启动完成！
echo.
echo 访问地址：
echo   前端：http://localhost:8000/
echo   API 文档：http://localhost:8000/docs
echo ========================================
pause