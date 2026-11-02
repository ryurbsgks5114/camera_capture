
@echo off
chcp 65001 > nul
setlocal

cd /d "%~dp0"

echo.
echo ========================================
echo   Camera Server 설치 프로그램
echo ========================================
echo.

set "PYTHON_CMD="

REM ========================================
REM 1. Python 3.14 설치 여부 확인
REM ========================================

echo [확인] Python 3.14 설치 여부를 확인합니다.

py -3.14 --version > nul 2>&1

if not errorlevel 1 (
    set "PYTHON_CMD=py -3.14"
    goto PYTHON_READY
)

python -c "import sys; sys.exit(0 if sys.version_info[:2] == (3,14) else 1)" > nul 2>&1

if not errorlevel 1 (
    set "PYTHON_CMD=python"
    goto PYTHON_READY
)

REM ========================================
REM 2. Python 자동 다운로드
REM ========================================

echo.
echo [안내] Python 3.14가 설치되어 있지 않습니다.
echo [진행] Python 3.14.3을 다운로드합니다.
echo.

set "INSTALLER=%TEMP%\python-3.14.3-amd64.exe"

powershell -NoProfile -ExecutionPolicy Bypass -Command "try { Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.14.3/python-3.14.3-amd64.exe' -OutFile '%INSTALLER%' -UseBasicParsing; exit 0 } catch { Write-Error $_; exit 1 }"

if errorlevel 1 (
    echo [설치 실패] Python 다운로드에 실패했습니다.
    pause
    exit /b 1
)

REM ========================================
REM 3. Python 자동 설치
REM ========================================

echo.
echo [진행] Python을 설치합니다.
echo.

"%INSTALLER%" /quiet InstallAllUsers=0 TargetDir="%LOCALAPPDATA%\Programs\Python\Python314" Include_pip=1 Include_launcher=0 PrependPath=0 Include_test=0

if errorlevel 1 (
    echo [설치 실패] Python 설치에 실패했습니다.
    pause
    exit /b 1
)

set "PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python314\python.exe""

if not exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" (
    echo [설치 실패] Python 실행 파일을 찾을 수 없습니다.
    pause
    exit /b 1
)

REM ========================================
REM 4. Python 설치 확인
REM ========================================

:PYTHON_READY

echo.
echo [확인] Python 설치 확인 완료
%PYTHON_CMD% --version

if errorlevel 1 (
    echo [설치 실패] Python 실행에 실패했습니다.
    pause
    exit /b 1
)

REM ========================================
REM 5. pip 업데이트
REM ========================================

echo.
echo [설치 중] pip 업데이트
%PYTHON_CMD% -m pip install --upgrade pip

if errorlevel 1 (
    echo [설치 실패] pip 업데이트에 실패했습니다.
    pause
    exit /b 1
)

REM ========================================
REM 6. 프로젝트 라이브러리 설치
REM ========================================

echo.
echo [설치 중] 필수 라이브러리 설치
%PYTHON_CMD% -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [설치 실패] 라이브러리 설치 중 오류가 발생했습니다.
    pause
    exit /b 1
)

REM ========================================
REM 7. 주요 라이브러리 확인
REM ========================================

echo.
echo [확인] 주요 라이브러리 작동 여부를 확인합니다.

%PYTHON_CMD% -c "import flask, flask_socketio, pythoncom, comgrab3; print('필수 라이브러리 확인 완료')"

if errorlevel 1 (
    echo.
    echo [설치 실패] 라이브러리 확인 중 오류가 발생했습니다.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Camera Server 설치 완료
echo ========================================
echo.
echo Python 및 필수 라이브러리 설치가 완료되었습니다.
echo.

pause
