@echo off
setlocal

set "FLASK_PY="

if exist ".\.venv\pyvenv.cfg" (
  for /f "tokens=2* delims==" %%A in ('findstr /b /c:"home = " ".\.venv\pyvenv.cfg"') do set "VENV_HOME=%%A"
  if defined VENV_HOME (
    set "VENV_HOME=%VENV_HOME:~1%"
    if exist "%VENV_HOME%\python.exe" (
      set "FLASK_PY=.\\.venv\Scripts\python.exe"
    )
  )
)

if not defined FLASK_PY if exist "C:\Users\Administrator\.venv-presensi\Scripts\python.exe" (
  set "FLASK_PY=C:\Users\Administrator\.venv-presensi\Scripts\python.exe"
)

if not defined FLASK_PY (
  set "FLASK_PY=python"
)

set "COMSPEC=%SystemRoot%\System32\cmd.exe"
set "PATH=%SystemRoot%\System32;%SystemRoot%;%SystemRoot%\System32\Wbem;%PATH%"

concurrently --shell "%SystemRoot%\System32\cmd.exe" -n flask,sync -c blue,green "%FLASK_PY% -m flask --app app:create_app --debug run --host 127.0.0.1 --port 5000" "wait-on tcp:127.0.0.1:5000 && browser-sync start --config bs-config.js"
