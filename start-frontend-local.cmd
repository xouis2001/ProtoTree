@echo off
setlocal
cd /d "%~dp0frontend"
set "PATH=C:\Program Files\nodejs;%PATH%"
if not exist "node_modules" (
  "C:\Program Files\nodejs\npm.cmd" install
)
"C:\Program Files\nodejs\npm.cmd" run dev -- --host 127.0.0.1
