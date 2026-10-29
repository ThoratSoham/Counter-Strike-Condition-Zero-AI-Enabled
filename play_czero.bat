@echo off
cd /d "%~dp0"
title Counter-Strike: Condition Zero (AI Teammates Mod)
echo ============================================================
echo   Counter-Strike: Condition Zero + AI Teammates Mod
echo   Starting AI Brain Service and Launching Game...
echo ============================================================

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py main.py --launch-game --no-ui
    goto :eof
)

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python main.py --launch-game --no-ui
    goto :eof
)

echo [ERROR] Python was not found on your PATH!
echo         Cannot start AI Brain Service. Launching Condition Zero in local fallback mode...
start "" "hl.exe" -game czero -nomaster -insecure +exec listenserver.cfg
pause
