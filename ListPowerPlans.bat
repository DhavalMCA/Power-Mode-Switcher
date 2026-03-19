@echo off
REM ============================================================================
REM List All Available Power Plans
REM ============================================================================

setlocal enabledelayedexpansion

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Please run this script as Administrator
    pause
    exit /b 1
)

cls
echo.
echo ============================================================
echo ALL AVAILABLE POWER PLANS ON YOUR SYSTEM
echo ============================================================
echo.

powercfg /list

echo.
echo ============================================================
echo CURRENT ACTIVE POWER PLAN
echo ============================================================
echo.

powercfg /getactivescheme

echo.
echo ============================================================
echo All power plans listed above. Use the GUID to switch modes.
echo ============================================================
echo.

pause
