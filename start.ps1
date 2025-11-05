# Script para iniciar Frontend e Backend simultaneamente
Write-Host "🚀 Iniciando Controle Financeiro..." -ForegroundColor Green
Write-Host ""

# Verificar se o venv existe
if (-not (Test-Path "backend\venv")) {
    Write-Host "❌ Ambiente virtual não encontrado!" -ForegroundColor Red
    Write-Host "Execute primeiro: cd backend; python -m venv venv; venv\Scripts\activate; pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# Verificar se node_modules existe (frontend)
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "⚠️  node_modules não encontrado. Instalando dependências do frontend..." -ForegroundColor Yellow
    Set-Location frontend
    npm install
    Set-Location ..
}

# Verificar se concurrently está instalado
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Instalando dependências do projeto..." -ForegroundColor Yellow
    npm install
}

# Iniciar ambos os servidores
Write-Host "🔧 Iniciando Backend e Frontend..." -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ URLs:" -ForegroundColor Green
Write-Host "📍 Frontend: http://localhost:5173" -ForegroundColor Yellow
Write-Host "📍 Backend API: http://localhost:8000" -ForegroundColor Yellow
Write-Host "📚 API Docs: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "Pressione Ctrl+C para parar ambos os servidores" -ForegroundColor Gray
Write-Host ""

npm start
