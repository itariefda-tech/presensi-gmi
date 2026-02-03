@echo off
setlocal

set "FLASK_PY="

if exist ".\.venv\pyvenv.cfg" (
  for /f "usebackq tokens=1* delims==" %%A in (".\.venv\pyvenv.cfg") do (
    if /I "%%A"=="home " (
      for /f "tokens=* delims= " %%H in ("%%B") do set "VENV_HOME=%%H"
    )
  )
  if defined VENV_HOME (
    if exist "%VENV_HOME%\python.exe" (
      set "FLASK_PY=.\\.venv\Scripts\python.exe"
    )
  )
)

if not defined FLASK_PY if exist "C:\Users\Administrator\.venv-presensi\Scripts\python.exe" (
  set "FLASK_PY=C:\Users\Administrator\.venv-presensi\Scripts\python.exe"
)

if not defined FLASK_PY set "FLASK_PY=python"

set "COMSPEC_PATH=%ComSpec%"
if not defined COMSPEC_PATH set "COMSPEC_PATH=C:\Windows\System32\cmd.exe"
if not exist "%COMSPEC_PATH%" set "COMSPEC_PATH=C:\Windows\Sysnative\cmd.exe"
if not exist "%COMSPEC_PATH%" set "COMSPEC_PATH=cmd.exe"

concurrently --shell "%COMSPEC_PATH%" -n flask,sync -c blue,green "%FLASK_PY% -m flask --app app:create_app --debug run --host 127.0.0.1 --port 5000" "wait-on tcp:127.0.0.1:5000 && browser-sync start --config bs-config.js"
