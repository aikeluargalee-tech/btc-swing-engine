@echo off
title BTC Pattern Dashboard (OKX 1h)
chcp 65001 >nul
cd /d "%~dp0"
call .\.venv\Scripts\python.exe btc_pattern_dashboard.py %*
if errorlevel 1 pause
