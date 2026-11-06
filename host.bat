@echo off
title CZ AI Teammates - Multiplayer Host (Server + AI Brain)
cd /d "%~dp0"

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py -u -m multiplayer.host_manager %*
) else (
    python -u -m multiplayer.host_manager %*
)

if %ERRORLEVEL% NEQ 0 pause

