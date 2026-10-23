@echo off
title Build Antigravity Desktop Pet .EXE
cd /d "%~dp0"

echo ========================================================
echo   Building Antigravity Desktop Pet Standalone App (.EXE)
echo ========================================================
echo.

:: Check python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH!
    pause
    exit /b 1
)

:: Ensure PyInstaller is installed
python -c "import PyInstaller" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [*] Installing PyInstaller...
    pip install pyinstaller
)

:: Ensure app icon exists
if not exist "assets\app_icon.ico" (
    echo [*] Generating app icon...
    python -c "from PIL import Image; import os; src = 'assets/hime_preview.png' if os.path.exists('assets/hime_preview.png') else 'assets/default_pet.png'; Image.open(src).save('assets/app_icon.ico', format='ICO', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])"
)

echo [*] Compiling standalone executable with PyInstaller...
pyinstaller --noconfirm --onedir --windowed ^
    --name "AntigravityPet" ^
    --icon "assets/app_icon.ico" ^
    --add-data "assets;assets" ^
    --add-data "settings.html;." ^
    main.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo   [SUCCESS] Build completed successfully!
    echo   Executable located at: dist\AntigravityPet\AntigravityPet.exe
    echo   You can zip 'dist\AntigravityPet' to share with users!
    echo ========================================================
    echo.
) else (
    echo.
    echo [ERROR] Build failed with error code %ERRORLEVEL%.
    echo.
)
pause
