@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Creating the local Python environment...
  where py >nul 2>nul
  if errorlevel 1 (
    python -m venv .venv
  ) else (
    py -3 -m venv .venv
  )
  if errorlevel 1 (
    echo Could not create the Python environment. Install Python 3 and try again.
    exit /b 1
  )
)
call ".venv\Scripts\activate.bat"
if errorlevel 1 exit /b 1
if not exist ".venv\packages-installed.txt" (
  echo Installing the required Python packages. This happens only on first launch...
  python -m pip install --upgrade pip
  if errorlevel 1 exit /b 1
  python -m pip install -r requirements.txt
  if errorlevel 1 (
    echo Package installation failed. Check your Internet connection and Python version.
    exit /b 1
  )
  echo Installed>".venv\packages-installed.txt"
)
exit /b 0
