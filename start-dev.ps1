$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $root 'backend'
$frontendDir = Join-Path $root 'frontend'
$backendPython = Join-Path $backendDir '.venv\Scripts\python.exe'

# Kill any lingering processes first
Get-Process python, node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

Start-Process powershell -NoNewWindow -ArgumentList '-NoExit', '-Command', "Set-Location '$backendDir'; & '$backendPython' -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
Start-Sleep -Seconds 2
Start-Process powershell -NoNewWindow -ArgumentList '-NoExit', '-Command', "Set-Location '$frontendDir'; npm run dev -- --host 0.0.0.0 --port 5173"

Write-Host ""
Write-Host "=========================================="
Write-Host "    DataInsight AI Started!"
Write-Host "=========================================="
Write-Host "Backend:  http://localhost:8000"
Write-Host "Frontend: http://localhost:5173"
Write-Host ""
Write-Host "Open http://localhost:5173 in your browser"
Write-Host "=========================================="
Write-Host ""
