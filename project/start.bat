@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Brak srodowiska .venv. Uruchom polecenia instalacyjne z README.md.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000
