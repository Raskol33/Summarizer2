@echo off
title YouTube Summarizer Launcher
echo ========================================
echo   YouTube Video Summarizer
echo   Launching application...
echo ========================================
echo.

cd /d "%~dp0"

python -m streamlit run app_final.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo   ERROR: Failed to launch the app
    echo   Make sure Python is installed
    echo ========================================
    echo.
    pause
)
