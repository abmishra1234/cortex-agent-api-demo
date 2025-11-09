@echo off
REM filepath: setup.bat
REM Batch Setup Script for Snowflake Cortex Agent Application
REM This script provides a simple interface for Windows Command Prompt users

setlocal enabledelayedexpansion

REM Check if PowerShell is available
where powershell >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: PowerShell is not available
    echo This script requires PowerShell to run
    exit /b 1
)

REM If no arguments, show help
if "%1"=="" (
    call :show_help
    exit /b 0
)

REM Parse arguments and call PowerShell script
if /I "%1"=="install" (
    powershell -ExecutionPolicy Bypass -File setup.ps1 -Install
    exit /b %ERRORLEVEL%
)

if /I "%1"=="run" (
    powershell -ExecutionPolicy Bypass -File setup.ps1 -Run
    exit /b %ERRORLEVEL%
)

if /I "%1"=="test" (
    powershell -ExecutionPolicy Bypass -File setup.ps1 -Test
    exit /b %ERRORLEVEL%
)

if /I "%1"=="clean" (
    powershell -ExecutionPolicy Bypass -File setup.ps1 -Clean
    exit /b %ERRORLEVEL%
)

if /I "%1"=="help" (
    call :show_help
    exit /b 0
)

if /I "%1"=="-h" (
    call :show_help
    exit /b 0
)

if /I "%1"=="/?" (
    call :show_help
    exit /b 0
)

echo Unknown command: %1
echo.
call :show_help
exit /b 1

:show_help
echo.
echo Snowflake Cortex Agent - Setup Script
echo ======================================
echo.
echo Usage: setup.bat [command]
echo.
echo Commands:
echo   install     Install all dependencies and setup environment
echo   run         Run the Streamlit application
echo   test        Run all tests with coverage
echo   clean       Clean up virtual environment and cache files
echo   help        Show this help message
echo.
echo Examples:
echo   setup.bat install    # First time setup
echo   setup.bat run        # Start the application
echo   setup.bat test       # Run tests
echo.
exit /b 0
