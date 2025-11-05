@echo off
chcp 65001 >nul
echo 🚀 Iniciando Controle Financeiro...
echo.

REM Verificar se o venv existe
if not exist "backend\venv" (
    echo ❌ Ambiente virtual não encontrado!
    echo Execute primeiro: cd backend ^&^& python -m venv venv ^&^& venv\Scripts\activate ^&^& pip install -r requirements.txt
    pause
    exit /b 1
)

REM Verificar se node_modules existe (frontend)
if not exist "frontend\node_modules" (
    echo ⚠️  node_modules não encontrado. Instalando dependências do frontend...
    cd frontend
    call npm install
    cd ..
)

REM Verificar se concurrently está instalado
if not exist "node_modules" (
    echo 📦 Instalando dependências do projeto...
    call npm install
)

REM Iniciar ambos os servidores
echo 🔧 Iniciando Backend e Frontend...
echo.
echo ✅ URLs:
echo 📍 Frontend: http://localhost:5173
echo 📍 Backend API: http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs
echo.
echo Pressione Ctrl+C para parar ambos os servidores
echo.

call npm start
