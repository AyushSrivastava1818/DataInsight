@echo off
setlocal
echo.
echo ==========================================
echo     DataInsight AI - Starting...
echo ==========================================
echo.

cd /d "%~dp0"

REM Kill any lingering processes
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
timeout /t 2 /nobreak >nul

REM Start backend
start "DataInsight Backend" cmd /k "cd /d "%~dp0backend" && .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend
start "DataInsight Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev -- --host 0.0.0.0 --port 5173"

echo.
echo ==========================================
echo    DataInsight AI Started!
echo ==========================================
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Opening browser in 5 seconds...
echo ==========================================
echo.

timeout /t 5 /nobreak >nul
start http://localhost:5173

