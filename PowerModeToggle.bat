@echo off
REM ============================================================================
REM Power Mode Toggle Script
REM Description: Toggles between Balanced and Ultimate Performance power modes
REM Author: Generated Script
REM Requirements: Must run as Administrator
REM ============================================================================

setlocal enabledelayedexpansion

REM ============================================================================
REM CHECK FOR ADMINISTRATOR PRIVILEGES
REM ============================================================================
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ============================================================
    echo ERROR: This script requires Administrator privileges!
    echo ============================================================
    echo.
    echo Please run this script as Administrator:
    echo 1. Right-click on PowerModeToggle.bat
    echo 2. Select "Run as administrator"
    echo.
    pause
    exit /b 1
)

REM ============================================================================
REM DEFINE POWER PLAN GUIDs
REM ============================================================================
REM Balanced Mode GUID (Microsoft Default)
set "BALANCED_GUID=381b4222-f694-41f0-9685-ff5bb260df2e"

REM Ultimate Performance Schema GUID (used to duplicate/enable the mode)
set "ULTIMATE_SCHEMA=e9a42b02-d5df-448d-aa00-03f14749eb61"

REM Auto-detect Ultimate Performance GUID from system
REM Token=4 because: token1=Power, token2=Scheme, token3=GUID:, token4=ACTUAL_GUID
for /f "tokens=4" %%A in ('powercfg /list ^| findstr "Ultimate"') do (
    set "ULTIMATE_GUID=%%A"
)

REM If Ultimate Performance not found, try High Performance as fallback
if "!ULTIMATE_GUID!"=="" (
    for /f "tokens=4" %%A in ('powercfg /list ^| findstr "High"') do (
        set "ULTIMATE_GUID=%%A"
        set "ULTIMATE_NAME=High Performance"
        goto :guid_detected
    )
)

:guid_detected

REM ============================================================================
REM GET CURRENT ACTIVE POWER PLAN
REM ============================================================================
echo.
echo ============================================================
echo Detecting current power plan...
echo ============================================================

REM Capture the current active scheme
for /f "tokens=*" %%A in ('powercfg /getactivescheme') do (
    set "ACTIVE_SCHEME=%%A"
)

REM Extract GUID from the output (format: "Power Scheme GUID: {guid}  (schemename)")
REM Use tokens=4 because: token1=Power, token2=Scheme, token3=GUID:, token4=ACTUAL_GUID
for /f "tokens=4" %%A in ('powercfg /getactivescheme') do (
    set "ACTIVE_GUID=%%A"
)

echo Current active power plan:
echo   Full Info: !ACTIVE_SCHEME!
echo   GUID: !ACTIVE_GUID!
echo.

REM ============================================================================
REM CHECK IF ULTIMATE PERFORMANCE MODE EXISTS
REM ============================================================================
echo Checking if Ultimate Performance mode is available...

REM If ULTIMATE_GUID is empty, try to enable the mode first
if "!ULTIMATE_GUID!"=="" (
    echo WARNING: Ultimate Performance GUID not found on system
    echo Attempting to enable it...
    powercfg -duplicatescheme !ULTIMATE_SCHEMA! >nul 2>&1
    
    if !errorlevel! equ 0 (
        echo ✓ Ultimate Performance mode enabled
        REM Re-detect GUID
        for /f "tokens=4" %%A in ('powercfg /list ^| findstr "Ultimate"') do (
            set "ULTIMATE_GUID=%%A"
        )
    ) else (
        echo ✗ Failed to enable Ultimate Performance mode
        echo.
        echo Available power plans on your system:
        powercfg /list
        echo.
        echo Note: If you only see Balanced, your Windows version may not support
        echo Ultimate Performance. Please check your Windows edition.
        echo.
        pause
        exit /b 2
    )
)

powercfg /query !ULTIMATE_GUID! >nul 2>&1

if %errorlevel% neq 0 (
    echo.
    echo WARNING: Ultimate Performance mode not found!
    echo Attempting to enable it by duplicating from schema...
    echo.
    
    powercfg -duplicatescheme !ULTIMATE_SCHEMA! >nul 2>&1
    
    if %errorlevel% equ 0 (
        echo ✓ Ultimate Performance mode has been enabled successfully!
        echo.
        REM Re-capture the new GUID
        for /f "tokens=4" %%A in ('powercfg /list ^| findstr "Ultimate"') do (
            set "ULTIMATE_GUID=%%A"
        )
    ) else (
        echo ✗ Failed to enable Ultimate Performance mode
        echo Please ensure you have the latest Windows updates installed
        echo.
        pause
        exit /b 2
    )
) else (
    echo ✓ Ultimate Performance mode is available
    echo.
)

REM ============================================================================
REM DETERMINE WHICH MODE TO SWITCH TO
REM ============================================================================

if "!ACTIVE_GUID!"=="!BALANCED_GUID!" (
    echo Current mode: BALANCED
    echo Switching to: ULTIMATE PERFORMANCE
    echo.
    powercfg /setactive !ULTIMATE_GUID!
    
    if %errorlevel% equ 0 (
        echo ✓ Successfully switched to ULTIMATE PERFORMANCE mode!
    ) else (
        echo ✗ Failed to switch to ULTIMATE PERFORMANCE mode
        pause
        exit /b 3
    )
    
) else if "!ACTIVE_GUID!"=="!ULTIMATE_GUID!" (
    echo Current mode: ULTIMATE PERFORMANCE
    echo Switching to: BALANCED
    echo.
    powercfg /setactive !BALANCED_GUID!
    
    if %errorlevel% equ 0 (
        echo ✓ Successfully switched to BALANCED mode!
    ) else (
        echo ✗ Failed to switch to BALANCED mode
        pause
        exit /b 3
    )
    
) else (
    echo Current mode: UNKNOWN (GUID: !ACTIVE_GUID!)
    echo Unable to identify current power plan as either Balanced or Ultimate Performance
    echo.
    pause
    exit /b 4
)

REM ============================================================================
REM VERIFY AND DISPLAY NEW ACTIVE POWER PLAN
REM ============================================================================
echo.
echo Verifying new power plan...

for /f "tokens=*" %%A in ('powercfg /getactivescheme') do (
    set "NEW_SCHEME=%%A"
)

echo New active power plan:
echo   !NEW_SCHEME!
echo.
echo ============================================================
echo SUCCESS: Power mode toggled successfully!
echo ============================================================
echo.

pause
exit /b 0
