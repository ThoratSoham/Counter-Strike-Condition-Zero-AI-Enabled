@echo off
cd /d "%~dp0"
title Counter-Strike: Condition Zero + AI Teammates

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    start "" py main.py --launch-game --no-ui
    exit
)

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    start "" python main.py --launch-game --no-ui
    exit
)

echo [WARNING] Python not detected on PATH. Launching Condition Zero without AI brain...
start "" "hl.exe" -game czero -gl -nomaster -insecure +exec listenserver.cfg
exit
