@echo off
:: Check if stunnel is installed (either in PATH or in the current directory)
IF EXIST "%~dp0stunnel.exe" (
    echo Found stunnel.exe in the current directory
    SET STUNNEL_PATH="%~dp0stunnel.exe"
) ELSE (
    where stunnel >nul 2>&1
    if %errorlevel% neq 0 (
        echo Error: stunnel is not installed or not in PATH
        echo Please install stunnel from https://www.stunnel.org/
        echo or place stunnel.exe in the current directory
        pause
        exit /b 1
    )
    SET STUNNEL_PATH=stunnel
)

:: Set environment variables for stunnel
set REMOTE_SSH_SERVER=your.server.com
set REMOTE_SSH_PORT=22

:: Start stunnel in background
echo Starting stunnel SSL/TLS tunnel...
start /B %STUNNEL_PATH% stunnel.conf

:: Start main application
echo Starting SSH Dynamic Proxy Tool...
start /B pythonw.exe main.py

pause
