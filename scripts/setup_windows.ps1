# PowerShell Setup Script for Real-Time People Counting and Crowd Density Estimation System
# Target OS: Windows 10/11
# Prerequisites: Python 3.10+ and Node.js 18+

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  Real-Time People Counting and Crowd Density Estimation System  " -ForegroundColor Cyan
Write-Host "            Windows Automated Environment Setup Script           " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

# 1. Check Python
Write-Host "`n[1/6] Checking Python installation..." -ForegroundColor Yellow
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Error "Python is not installed or not in PATH. Please install Python 3.10+ from python.org."
    exit 1
}
$pyVer = python --version
Write-Host "  Found: $pyVer" -ForegroundColor Green

# 2. Check Node & npm
Write-Host "`n[2/6] Checking Node.js and npm..." -ForegroundColor Yellow
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeCmd) {
    Write-Error "Node.js is not found. Please install Node.js (v18+ recommended) from nodejs.org."
    exit 1
}
$nodeVer = node --version
$npmVer = npm --version
Write-Host "  Found Node: $nodeVer | npm: $npmVer" -ForegroundColor Green

# 3. Backend Dependencies
Write-Host "`n[3/6] Verifying & installing backend dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install Python requirements."
    exit 1
}
Write-Host "  Backend Python packages verified." -ForegroundColor Green

# 4. Frontend Dependencies
Write-Host "`n[4/6] Installing frontend dependencies..." -ForegroundColor Yellow
Push-Location frontend
npm install
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Frontend build had warnings. Verify node_modules."
} else {
    Write-Host "  Frontend React/Vite packages compiled successfully." -ForegroundColor Green
}
Pop-Location

# 5. Generate Built-in Sample Video
Write-Host "`n[5/6] Verifying demonstration sample media..." -ForegroundColor Yellow
python scripts/generate_sample_video.py --output datasets/sample/crowd_sample.mp4 --num-people 16 --duration-sec 10
Write-Host "  Sample crowd video ready at datasets/sample/crowd_sample.mp4" -ForegroundColor Green

# 6. Run Automated Test Suite
Write-Host "`n[6/6] Running automated test verification..." -ForegroundColor Yellow
python -m pytest backend/tests -v
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Some tests encountered issues. Review logs."
} else {
    Write-Host "  All test verification passed!" -ForegroundColor Green
}

Write-Host "`n=================================================================" -ForegroundColor Cyan
Write-Host "  Setup Complete! To start the application:                      " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "Terminal 1 (Backend):" -ForegroundColor White
Write-Host "  python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload`n" -ForegroundColor Yellow

Write-Host "Terminal 2 (Frontend):" -ForegroundColor White
Write-Host "  cd frontend" -ForegroundColor Yellow
Write-Host "  npm run dev`n" -ForegroundColor Yellow

Write-Host "Open Dashboard: http://localhost:5173" -ForegroundColor Green
Write-Host "Swagger Docs:   http://127.0.0.1:8000/docs`n" -ForegroundColor Green
