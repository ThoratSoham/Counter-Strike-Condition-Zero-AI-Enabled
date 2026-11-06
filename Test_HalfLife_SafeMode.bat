@echo off
cd /d "%~dp0"
title Half-Life (Diagnostic Safe Mode)
echo Launching Half-Life in Diagnostic Safe Mode...
start "" "hl.exe" -game valve -soft -windowed -w 800 -h 600 -nosound -nofbo

