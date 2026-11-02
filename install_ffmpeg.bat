
@echo off
chcp 65001 > nul
setlocal

cd /d "%~dp0"

echo.
echo ========================================
echo   FFmpeg 설치 프로그램
echo ========================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_ffmpeg.ps1"

if errorlevel 1 (
    echo.
    echo [설치 실패] FFmpeg 설치 중 오류가 발생했습니다.
    echo.
    pause
    exit /b 1
)

echo.
echo FFmpeg 설치 및 환경 변수 확인이 완료되었습니다.
echo.

pause
