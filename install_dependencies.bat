
@echo off
setlocal
cd /d "%~dp0"

echo.
echo ========================================
echo   Camera Server Setup
echo ========================================
echo.

set "PYTHON_EXE="
set "PYTHON_DIR="
set "PYTHON_SCRIPTS="

REM ========================================
REM 1. Detect Python 3.14
REM ========================================

echo [INFO] Checking Python 3.14...

REM Check Python Launcher
for /f "delims=" %%I in ('py -3.14 -c "import sys; print(sys.executable)" 2^>nul') do set "PYTHON_EXE=%%I"

if defined PYTHON_EXE goto PYTHON_READY

REM Check Python command
for /f "delims=" %%I in ('python -c "import sys; print(sys.executable if sys.version_info[:2] == (3,14) else '')" 2^>nul') do set "PYTHON_EXE=%%I"

if defined PYTHON_EXE goto PYTHON_READY

REM Check default installation directory
set "PYTHON_DIR=%LOCALAPPDATA%\Programs\Python\Python314"
set "PYTHON_EXE=%PYTHON_DIR%\python.exe"

if exist "%PYTHON_EXE%" (
    echo [INFO] Existing Python installation found.
    goto PYTHON_READY
)

set "PYTHON_EXE="

REM ========================================
REM 2. Download Python
REM ========================================

echo.
echo [INFO] Python 3.14 was not found.
echo [INFO] Downloading Python 3.14.3...
echo.

set "INSTALLER=%TEMP%\python-3.14.3-amd64.exe"
set "PYTHON_DIR=%LOCALAPPDATA%\Programs\Python\Python314"

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "try { Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.14.3/python-3.14.3-amd64.exe' -OutFile '%INSTALLER%' -UseBasicParsing; exit 0 } catch { Write-Error $_; exit 1 }"

if errorlevel 1 (
    echo [ERROR] Failed to download Python.
    pause
    exit /b 1
)

REM ========================================
REM 3. Install Python
REM ========================================

echo.
echo [INFO] Installing Python...
echo.

"%INSTALLER%" /quiet InstallAllUsers=0 TargetDir="%PYTHON_DIR%" Include_pip=1 Include_launcher=0 PrependPath=0 Include_test=0

if errorlevel 1 (
    echo [ERROR] Python installation failed.
    pause
    exit /b 1
)

set "PYTHON_EXE=%PYTHON_DIR%\python.exe"

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python executable was not found.
    pause
    exit /b 1
)

REM ========================================
REM 4. Verify Python
REM ========================================

:PYTHON_READY

if not defined PYTHON_EXE (
    echo [ERROR] Python executable path is missing.
    pause
    exit /b 1
)

for %%I in ("%PYTHON_EXE%") do set "PYTHON_DIR=%%~dpI"

if "%PYTHON_DIR:~-1%"=="\" set "PYTHON_DIR=%PYTHON_DIR:~0,-1%"

set "PYTHON_SCRIPTS=%PYTHON_DIR%\Scripts"

echo.
echo [INFO] Checking Python installation...

"%PYTHON_EXE%" --version

if errorlevel 1 (
    echo [ERROR] Python execution failed.
    pause
    exit /b 1
)

REM ========================================
REM 5. Register Python in User PATH
REM ========================================

echo.
echo [INFO] Registering Python paths...

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$dirs = @($env:PYTHON_DIR, $env:PYTHON_SCRIPTS); $userPath = [Environment]::GetEnvironmentVariable('Path', 'User'); $parts = @($userPath -split ';' | Where-Object { $_ -and $_.Trim() }); foreach ($dir in $dirs) { if (Test-Path -LiteralPath $dir) { $exists = $false; foreach ($part in $parts) { if ($part.Trim().TrimEnd('\') -ieq $dir.TrimEnd('\')) { $exists = $true; break } }; if (-not $exists) { $parts += $dir } } }; [Environment]::SetEnvironmentVariable('Path', ($parts -join ';'), 'User')"

if errorlevel 1 (
    echo [ERROR] Failed to register Python PATH.
    pause
    exit /b 1
)

REM Apply PATH to current setup process
set "PATH=%PYTHON_DIR%;%PYTHON_SCRIPTS%;%PATH%"

echo [INFO] Python PATH registration completed.

REM ========================================
REM 6. Upgrade pip
REM ========================================

echo.
echo [INFO] Upgrading pip...

"%PYTHON_EXE%" -m pip install --upgrade pip

if errorlevel 1 (
    echo [ERROR] Failed to upgrade pip.
    pause
    exit /b 1
)

REM ========================================
REM 7. Install Requirements
REM ========================================

echo.
echo [INFO] Installing project requirements...

"%PYTHON_EXE%" -m pip install -r requirements.txt

if errorlevel 1 (
    echo [ERROR] Failed to install project requirements.
    pause
    exit /b 1
)

REM ========================================
REM 8. Verify Required Libraries
REM ========================================

echo.
echo [INFO] Verifying required libraries...

"%PYTHON_EXE%" -c "import flask, flask_socketio, pythoncom, comgrab3; print('Required libraries are ready.')"

if errorlevel 1 (
    echo [ERROR] Required library verification failed.
    pause
    exit /b 1
)

REM ========================================
REM 9. Complete
REM ========================================

echo.
echo ========================================
echo   Setup Completed Successfully
echo ========================================
echo.
echo Python and required libraries are installed.
echo Open a NEW CMD or PowerShell window to use Python.
echo.

pause
