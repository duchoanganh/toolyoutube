@echo off
title TubeAuto Ultimate - Khởi Động
echo ==============================================
echo        TUBEAUTO ULTIMATE - AI STUDIO
echo ==============================================
echo.
echo [1/3] Đang khoi dong Backend Server (port 5000)...
start "Backend API (TubeAuto)" cmd /k "chcp 65001 >nul && set PYTHONIOENCODING=utf-8 && python server.py"

echo [2/3] Đang khoi dong Frontend Server (port 8000)...
start "Frontend UI (TubeAuto)" cmd /k "python -m http.server 8000"

echo [3/3] Cho 3 giay de may chu san sang...
timeout /t 3 /nobreak >nul

echo Hoan thanh! Đang mo trinh duyet...
start http://localhost:8000/tubeauto-ultimate.html
exit
