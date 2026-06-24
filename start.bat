@echo off
chcp 65001 >nul
echo ========================================
echo   Agentic RAG 智能问答系统启动脚本
echo   架构: Node.js 接入层 + Python 模型层
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未安装 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

REM 检查 Node.js 是否安装
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未安装 Node.js，请先安装 Node.js 18+
    pause
    exit /b 1
)

REM ==================== Python 模型层 ====================
echo [1/3] 检查 Python 模型层依赖...
cd backend
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements.txt >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Python 依赖安装失败
    pause
    exit /b 1
)
echo [√] Python 模型层依赖完成
cd ..

REM ==================== Node.js 接入层 ====================
echo.
echo [2/3] 检查 Node.js 接入层依赖...
cd node-server
if not exist "node_modules" (
    echo 安装 Node.js 依赖...
    call npm install
)
echo [√] Node.js 接入层依赖完成
cd ..

REM ==================== 前端 ====================
echo.
echo [3/3] 检查前端依赖...
cd frontend
if not exist "node_modules" (
    echo 安装前端依赖...
    call npm install
)
echo [√] 前端依赖完成
cd ..

REM ==================== 启动服务 ====================
echo.
echo ========================================
echo   启动服务...
echo ========================================
echo.
echo Python 模型层:  http://localhost:8000 (内部)
echo Node.js 接入层: http://localhost:3001
echo 前端界面:      http://localhost:3000
echo.
echo 按 Ctrl+C 停止所有服务
echo.

REM 启动 Python 模型层 (后台)
start "Python模型层" cmd /k "cd backend && call venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

REM 等待 Python 启动
echo 等待 Python 模型层启动...
timeout /t 3 /nobreak >nul

REM 启动 Node.js 接入层 (后台)
start "Node接入层" cmd /k "cd node-server && npx tsx src/index.ts"

REM 等待 Node.js 启动
timeout /t 2 /nobreak >nul

REM 启动前端
start "前端" cmd /k "cd frontend && npm run dev"

echo.
echo [√] 所有服务已启动！
echo.
echo   架构说明:
echo     前端 (Vue.js)   →  Node.js 接入层  →  Python 模型层
echo     localhost:3000    localhost:3001      localhost:8000
echo.
pause