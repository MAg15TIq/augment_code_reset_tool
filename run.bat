@echo off
REM Free AugmentCode Data Cleaner - Windows Launcher
REM This batch file makes it easy to run the application on Windows

title Free AugmentCode Data Cleaner

echo.
echo ================================================
echo Free AugmentCode Data Cleaner - Windows Launcher
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.7 or higher from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo Python found. Starting application...
echo.

REM Run the application
python run.py

REM Keep window open if there was an error
if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)

exit /b 0
