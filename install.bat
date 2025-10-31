@echo off
REM vim-dashboard installation script for Windows
REM This script sets up the virtual environment and installs dependencies

echo vim-dashboard Installation Script for Windows
echo ==========================================

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    python3 --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo Error: Python 3 not found. Please install Python 3.7 or later.
        echo Download from: https://www.python.org/downloads/
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=python3
    )
) else (
    set PYTHON_CMD=python
)

echo Using Python: %PYTHON_CMD%

REM Run the Python installation script
%PYTHON_CMD% install.py

if %errorlevel% neq 0 (
    echo Installation failed!
    pause
    exit /b 1
)

echo.
echo Installation completed successfully!
pause