@echo off
cd /d "%~dp0"
if exist "C:\Users\rain\AppData\Local\Programs\Python\Python311\python.exe" (
    start "" "C:\Users\rain\AppData\Local\Programs\Python\Python311\python.exe" main.py
) else if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    start "" "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" main.py
) else (
    start "" python main.py
)
