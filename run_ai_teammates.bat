@echo off
title AI Teammates for Counter-Strike: Condition Zero
echo ============================================================
echo   AI Teammates for Counter-Strike: Condition Zero
echo   Starting AI Brain Service and Command Center...
echo ============================================================
echo.

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py main.py
) else (
    python main.py
)

pause
