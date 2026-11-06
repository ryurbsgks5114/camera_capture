@echo off
setlocal
chcp 65001 > nul
title Camera Capture Server

REM Move to the folder containing this batch file.
cd /d "%~dp0"

REM Use the installed Python 3.14 executable.
set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"

echo ==========================================
echo        Camera Capture Server
echo ==========================================
echo.

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python 3.14 was not found.
    echo Expected path:
    echo %PYTHON_EXE%
    echo.
    echo Check the Python installation path.
    pause
    exit /b 1
)

if not exist "%~dp0server.py" (
    echo [ERROR] server.py was not found in this folder.
    echo Place this batch file in the camera_capture server folder.
    echo.
    pause
    exit /b 1
)

echo Server folder: %~dp0
echo Python: %PYTHON_EXE%
echo.
echo Starting server...
echo To stop the server, press Ctrl+C in this window.
echo ==========================================
echo.

"%PYTHON_EXE%" "%~dp0server.py"

echo.
echo ==========================================
echo Server process has ended.
echo ==========================================
pause
endlocal
