@echo off
title BTC-USD Spot Swing Engine (11 Desks Live HUD)
chcp 65001 >nul
cd /d "%~dp0"
call .\.venv\Scripts\python.exe main.py %*
if errorlevel 1 pause
