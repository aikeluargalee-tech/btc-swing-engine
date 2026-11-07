@echo off
title BTC Swing Mobile Gateway (Setup B)
cd /d "%~dp0"
echo ========================================================
echo   BTC SWING ENGINE — MOBILE API & PWA SERVER (SETUP B)
echo ========================================================
echo.
echo Local Web Access : http://localhost:8080
echo Phone Wi-Fi Access: http://[YOUR-PC-LOCAL-IP]:8080
echo.
echo Serving Option 2: Unified Mobile Cockpit & 1 Hz WebSocket Stream
echo Press Ctrl+C to terminate the server.
echo.
.\.venv\Scripts\python.exe -m uvicorn api.mobile_server:app --host 0.0.0.0 --port 8080
pause
