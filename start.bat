@echo off
echo ========================================
echo   Agentic RAG 智能问答系统启动脚本
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未安装 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

REM 检查后端依赖
echo [1/3] 检查后端依赖...
cd backend
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境并安装依赖
call venv\Scripts\activate.bat
pip install -r requirements.txt >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 后端依赖安装失败
    pause
    exit /b 1
)
echo [✓] 后端依赖安装完成

REM 返回项目根目录
cd ..

REM 检查前端依赖
echo.
echo [2/3] 检查前端依赖...
cd frontend
if not exist "node_modules" (
    echo 安装前端依赖...
    call npm install
)
echo [✓] 前端依赖检查完成

REM 返回项目根目录
cd ..

REM 启动服务
echo.
echo ========================================
echo   启动服务...
echo ========================================
echo.
echo 后端 API: http://localhost:8000
echo 前端界面: http://localhost:3000
echo API文档:  http://localhost:8000/docs
echo.
echo 按 Ctrl+C 停止服务
echo.

REM 启动后端 (后台)
start "Backend" cmd /k "cd backend && call venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

REM 等待后端启动
timeout /t 3 /nobreak >nul

REM 启动前端
start "Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo [✓] 所有服务已启动！
pause
