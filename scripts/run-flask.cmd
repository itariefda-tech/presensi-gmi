@echo off
setlocal

set "FLASK_PY="

if exist "C:\Users\Administrator\.venv-presensi\Scripts\python.exe" (
  set "FLASK_PY=C:\Users\Administrator\.venv-presensi\Scripts\python.exe"
)

if not defined FLASK_PY if exist ".\.venv\pyvenv.cfg" (
  for /f "usebackq tokens=1* delims==" %%A in (".\.venv\pyvenv.cfg") do (
    if /I "%%A"=="home " (
      for /f "tokens=* delims= " %%H in ("%%B") do set "VENV_HOME=%%H"
    )
  )
  if defined VENV_HOME (
    if exist "%VENV_HOME%\python.exe" (
      set "FLASK_PY=.\.venv\Scripts\python.exe"
    )
  )
)

if not defined FLASK_PY set "FLASK_PY=python"

set "COMSPEC=%SystemRoot%\System32\cmd.exe"
set "PATH=%SystemRoot%\System32;%SystemRoot%;%SystemRoot%\System32\Wbem;%PATH%"

if not defined FLASK_SECRET (
  if exist "%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" (
    for /f %%S in ('%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe -NoProfile -Command "[guid]::NewGuid()"') do set "FLASK_SECRET=%%S"
  )
  if not defined FLASK_SECRET set "FLASK_SECRET=dev-%RANDOM%-%RANDOM%-%RANDOM%-%RANDOM%-%RANDOM%-%RANDOM%-%RANDOM%-%RANDOM%"
  if defined FLASK_SECRET (
    echo Generated FLASK_SECRET for this dev session.
  ) else (
    echo Failed to generate FLASK_SECRET. Set FLASK_SECRET manually.
    exit /b 1
  )
)

set "OWNER_ADDON_GENERATED="
if not defined OWNER_ADDON_PASSWORD (
  set "OWNER_ADDON_GENERATED=1"
  set "OWNER_ADDON_PASSWORD=owner123"
)
if defined OWNER_ADDON_GENERATED call echo Using OWNER_ADDON_PASSWORD for this dev session: %%OWNER_ADDON_PASSWORD%%

"%FLASK_PY%" -m flask --app app:create_app --debug run --host 127.0.0.1 --port 5000
