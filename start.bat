@echo off
REM Cross-Save Converter - Launcher for Windows
title Cross-Save Converter (Console <-> PC)

cd /d "%~dp0"

echo ==========================================================
echo   Cross-Save Converter (Console ^<^-^> PC) - Web UI
echo ==========================================================

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [-] Errore: Python non trovato nel PATH.
    echo     Scarica e installa Python da https://www.python.org/
    echo     Assicurati di spuntare "Add Python to PATH" durante l'installazione!
    pause
    exit /b 1
)

if not exist "venv" (
    echo [*] Creazione ambiente virtuale (venv)...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo [*] Verifica dipendenze (Flask, pyooz)...
pip install -q -r requirements.txt

echo [*] Avvio Web UI...
call venv\Scripts\python.exe app.py

pause
