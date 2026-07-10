@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv" (
  python -m venv .venv
)
".venv\Scripts\python.exe" -m pip install -r "backend\requirements-local.txt"
cd /d "%~dp0backend"
"..\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8001
