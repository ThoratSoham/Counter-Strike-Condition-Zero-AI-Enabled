@echo off
title CZ AI Teammates - One-Click Installer (Single-Player + Multiplayer)
cd /d "%~dp0"

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py -u -m multiplayer.installer_mp %*
) else (
    python -u -m multiplayer.installer_mp %*
)

echo.
pause

