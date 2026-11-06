@echo off
title CZ AI Teammates - Join Friend's Match
cd /d "%~dp0"

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py -u -m multiplayer.join_helper %*
) else (
    python -u -m multiplayer.join_helper %*
)

if %ERRORLEVEL% NEQ 0 pause

