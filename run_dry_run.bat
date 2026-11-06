@echo off
title BTC-USD Spot Swing Engine (Dry-Run Verification)
chcp 65001 >nul
cd /d "%~dp0"
call .\.venv\Scripts\python.exe main.py --dry-run --duration 3 --tab 0 %*
pause
