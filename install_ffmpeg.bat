
@echo off
setlocal

cd /d "%~dp0"

echo.
echo ========================================
echo   FFmpeg Installation
echo ========================================
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_ffmpeg.ps1"

if errorlevel 1 (
    echo.
    echo [ERROR] FFmpeg installation failed.
    echo.
    pause
    exit /b 1
)

echo.
echo FFmpeg installation and environment variable setup completed.
echo.

pause
