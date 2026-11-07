@echo off
rem Starts the audit web interface (http://127.0.0.1:8765). First start creates .venv.
rem Stop with Ctrl+C in this window. If port 8765 is busy, close the other run.cmd or use: run.cmd --port 8766
setlocal
cd /d "%~dp0"
set "VPY=.venv\Scripts\python.exe"
if exist "%VPY%" goto deps

set "PY=python"
where py >nul 2>&1 && set "PY=py -3"
%PY% -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 (
  echo Python 3.10+ not found. Install it from https://www.python.org/downloads/ and run again.
  pause
  exit /b 1
)
echo First start: creating .venv ...
%PY% -m venv .venv
if errorlevel 1 goto fail

:deps
fc /b requirements.txt .venv\requirements.installed >nul 2>&1
if not errorlevel 1 goto start
echo Installing requirements ...
"%VPY%" -m pip install --disable-pip-version-check -q -r requirements.txt
if errorlevel 1 goto fail
copy /y requirements.txt .venv\requirements.installed >nul

:start
"%VPY%" -m webapp %*
exit /b %errorlevel%

:fail
echo Setup failed - see the messages above.
pause
exit /b 1
