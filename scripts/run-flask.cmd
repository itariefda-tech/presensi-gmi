@echo off
setlocal

if exist ".\.venv\Scripts\python.exe" (
  set "FLASK_PY=.\\.venv\Scripts\python.exe"
) else (
  set "FLASK_PY=python"
)

set "COMSPEC=%SystemRoot%\System32\cmd.exe"
set "PATH=%SystemRoot%\System32;%SystemRoot%;%SystemRoot%\System32\Wbem;%PATH%"

"%FLASK_PY%" -m flask --app app:create_app --debug run --host 127.0.0.1 --port 5000
