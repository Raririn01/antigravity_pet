@echo off
title Antigravity Desktop Pet
cd /d "%~dp0"

python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in your system PATH.
    echo Please install Python 3.10+ from https://www.python.org/
    echo.
    pause
    exit /b 1
)

python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================================
    echo   Desktop Pet exited with error code %ERRORLEVEL%
    echo   If this is your first time, please run 'install.bat'
    echo   or execute: pip install -r requirements.txt
    echo ========================================================
    echo.
    pause
)
