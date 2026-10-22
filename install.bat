@echo off
title Install Antigravity Desktop Pet Dependencies
cd /d "%~dp0"

echo ========================================================
echo   Installing Antigravity Desktop Pet Dependencies...
echo ========================================================
echo.

python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found in PATH!
    echo Please install Python 3.10+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo   [SUCCESS] Dependencies installed successfully!
    echo   You can now launch the pet by running 'run_pet.bat'.
    echo ========================================================
) else (
    echo.
    echo ========================================================
    echo   [ERROR] Installation failed.
    echo   Please check your internet connection or Python setup.
    echo ========================================================
)

echo.
pause
