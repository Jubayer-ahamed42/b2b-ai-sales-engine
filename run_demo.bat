@echo off
setlocal
title B2B AI Sales Agent Client Demo Sandbox

set "PROJECT_DIR=C:\MY PROJECT\12. B2B AI SALES ENGINE & CLIENT DEMO SANDBOX"
cd /d "%PROJECT_DIR%"

echo ============================================================
echo 🚀 LAUNCHING B2B AI SALES ENGINE & CLIENT DEMO SANDBOX
echo ============================================================
echo [Be Smart With AI Agency Platform]
echo.

REM 1. Locate Python
set "PYTHON_EXE=python"
python --version >nul 2>&1
if errorlevel 1 (
    if exist "C:\Users\ASSDI\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
        set "PYTHON_EXE=C:\Users\ASSDI\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    ) else (
        echo [ERROR] Python not found in system PATH.
        pause
        exit /b 1
    )
)

echo [INFO] Starting Local Demo Server on http://127.0.0.1:5050 ...
echo [INFO] Opening Browser Sandbox Interface...

REM 2. Open browser after 2 seconds in parallel
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:5050"

REM 3. Run server
"%PYTHON_EXE%" server.py 5050

pause
