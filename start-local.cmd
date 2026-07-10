@echo off
setlocal
cd /d "%~dp0"
start "ProtoTree Backend" "%~dp0start-backend-local.cmd"
start "ProtoTree Frontend" "%~dp0start-frontend-local.cmd"
