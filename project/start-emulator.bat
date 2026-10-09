@echo off
setlocal
cd /d "%~dp0"
set "VOLTVAULT_EMULATOR=1"
if not defined VOLTVAULT_RESTART_DELAY set "VOLTVAULT_RESTART_DELAY=30"
if not exist .venv\Scripts\python.exe (
  echo Tworzenie lokalnego srodowiska Pythona...
  py -3 -m venv .venv
  if errorlevel 1 goto :python_error
)
if not exist .venv\Scripts\uvicorn.exe (
  if exist wheelhouse (
    echo Instalowanie zaleznosci z lokalnego wheelhouse...
    .venv\Scripts\python.exe -m pip install --no-index --find-links wheelhouse -r requirements.txt
  ) else (
    echo Pierwsze uruchomienie wymaga pobrania pakietow Python.
    .venv\Scripts\python.exe -m pip install -r requirements.txt
  )
  if errorlevel 1 goto :install_error
)
echo.
echo Emulator VoltVault dziala w trybie Windows.
echo Wirtualna karta i dane: %CD%\emulator_sd
echo Adres panelu: http://127.0.0.1:8000/
echo Zamknij to okno lub wcisnij Ctrl+C, aby zatrzymac emulator.
echo.
start "" http://127.0.0.1:8000/
.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
pause
exit /b %errorlevel%
:python_error
echo Nie znaleziono Pythona. Zainstaluj Python 3.10 lub nowszy i zaznacz opcje dodania do PATH.
pause
exit /b 1
:install_error
echo Instalacja zaleznosci nie powiodla sie. Sprawdz polaczenie lub katalog wheelhouse.
pause
exit /b 1
