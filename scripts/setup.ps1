# SatQuery AI — PowerShell Setup Script (Windows)
# Run from the satquery-ai/ root directory

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SatQuery AI — Stage 1 Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Check Node
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✓ Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Node.js not found. Install Node.js 20+" -ForegroundColor Red
    exit 1
}

# Copy .env if not exists
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "✓ Created .env from .env.example" -ForegroundColor Green
    Write-Host "  Please edit .env with your settings before running." -ForegroundColor Yellow
} else {
    Write-Host "✓ .env already exists" -ForegroundColor Green
}

# Create required directories
$dirs = @(
    "data\raw", "data\interim", "data\processed", "data\samples", "data\manifests",
    "models\trained\rs_vlm_lora", "models\grounding", "models\segmentation",
    "docs", "backend\uploads", "backend\outputs"
)
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "✓ Created $dir" -ForegroundColor Green
    }
}

# Backend setup
Write-Host "`n--- Backend Setup ---" -ForegroundColor Cyan
Set-Location backend

if (-not (Test-Path ".venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet

Write-Host "✓ Backend dependencies installed" -ForegroundColor Green
Set-Location ..

# Frontend setup
Write-Host "`n--- Frontend Setup ---" -ForegroundColor Cyan
Set-Location frontend
Write-Host "Installing Node dependencies..." -ForegroundColor Yellow
npm install --silent
Write-Host "✓ Frontend dependencies installed" -ForegroundColor Green
Set-Location ..

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To run the backend:" -ForegroundColor White
Write-Host "  cd backend" -ForegroundColor Gray
Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "  uvicorn app.main:app --reload --port 8000" -ForegroundColor Gray
Write-Host ""
Write-Host "To run the frontend:" -ForegroundColor White
Write-Host "  cd frontend" -ForegroundColor Gray
Write-Host "  npm run dev" -ForegroundColor Gray
Write-Host ""
Write-Host "API docs: http://localhost:8000/docs" -ForegroundColor Blue
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Blue
