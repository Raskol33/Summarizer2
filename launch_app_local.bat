@echo off
title YouTube Summarizer LOCAL Launcher
echo ========================================
echo   YouTube Video Summarizer - VERSION LOCALE
echo   100%% prive - Donnees sur votre serveur
echo ========================================
echo.

cd /d "%~dp0"

python -m streamlit run app_local.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo   ERREUR: Impossible de lancer l'app
    echo   Verifiez que Python est installe
    echo ========================================
    echo.
    pause
)
