@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" iniciar.py
  goto finish
)
if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
  "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" iniciar.py
  goto finish
)
py -3 -c "import sys; sys.exit(sys.version_info < (3,12))" >nul 2>&1
if not errorlevel 1 (
  py -3 iniciar.py
  goto finish
)
python -c "import sys; sys.exit(sys.version_info < (3,12))" >nul 2>&1
if not errorlevel 1 (
  python iniciar.py
  goto finish
)
echo Instale Python 3.12 ou superior em https://www.python.org/downloads/
:finish
pause
