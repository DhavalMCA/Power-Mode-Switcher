@echo off
REM ============================================================================
REM Power Plan Diagnostics Script
REM Description: Helps diagnose power plan issues and auto-configure PowerModeToggle.bat
REM Requirements: Must run as Administrator
REM ============================================================================

setlocal enabledelayedexpansion

REM Check for admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Please run this script as Administrator
    pause
    exit /b 1
)

cls
echo.
echo ============================================================
echo POWER MODE TOGGLE - DIAGNOSTIC REPORT
echo ============================================================
echo.

echo [1/5] Checking Windows Version...
wmic os get caption /value | find "Caption=" 
echo.

echo [2/5] Listing All Available Power Plans...
powercfg /list
echo.

echo [3/5] Current Active Power Plan...
powercfg /getactivescheme
echo.

echo [4/5] Detecting Ultimate Performance GUID...
REM Find Ultimate Performance GUID
for /f "tokens=4" %%A in ('powercfg /list ^| findstr "Ultimate"') do (
    set "ULTIMATE_GUID=%%A"
    goto :found_ultimate
)

:not_found
echo ✗ Ultimate Performance mode NOT FOUND
echo   Attempting to enable it...
powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61 >nul 2>&1
if %errorlevel% equ 0 (
    echo   ✓ Successfully enabled Ultimate Performance mode
    REM Re-check for the GUID
    for /f "tokens=4" %%A in ('powercfg /list ^| findstr "Ultimate"') do (
        set "ULTIMATE_GUID=%%A"
        goto :found_ultimate
    )
) else (
    echo   ✗ Failed to enable Ultimate Performance mode
    echo   Your Windows installation may not support this power plan
    goto :skip_update
)

:found_ultimate
echo ✓ Ultimate Performance GUID found: !ULTIMATE_GUID!
echo.

REM Ask user if they want to auto-update PowerModeToggle.bat
echo [5/5] Auto-Update Configuration...
echo.
echo Would you like to automatically update PowerModeToggle.bat with your system's GUIDs?
echo.
echo Current Settings to be Applied:
echo   - Balanced GUID: 381b4222-f694-41f0-9685-ff5bb260df2e
echo   - Ultimate Performance GUID: !ULTIMATE_GUID!
echo.
set /p UPDATE="Auto-update PowerModeToggle.bat? (Y/N): "

if /i "%UPDATE%"=="Y" (
    goto :update_script
) else (
    goto :skip_update
)

:update_script
echo.
echo Updating PowerModeToggle.bat...

REM Create a temporary script with updated GUIDs
setlocal enabledelayedexpansion
set "TEMP_FILE=%TEMP%\PowerModeToggle_temp.bat"
set "SCRIPT_FILE=PowerModeToggle.bat"

REM Read and replace GUIDs in PowerModeToggle.bat
for /f "delims=" %%A in ('type %SCRIPT_FILE%') do (
    set "LINE=%%A"
    
    REM Check if line contains ULTIMATE_GUID assignment
    echo !LINE! | find "ULTIMATE_GUID=" >nul
    if !errorlevel! equ 0 (
        echo set "ULTIMATE_GUID=!ULTIMATE_GUID!" >> %TEMP_FILE%
    ) else (
        echo !LINE! >> %TEMP_FILE%
    )
)

REM Replace original file
move /y %TEMP_FILE% %SCRIPT_FILE% >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ PowerModeToggle.bat has been successfully updated!
    echo.
    echo Updated Settings:
    echo   Ultimate Performance GUID: !ULTIMATE_GUID!
) else (
    echo ✗ Failed to update PowerModeToggle.bat
    echo   Please manually update the GUID in PowerModeToggle.bat
)
goto :end_diagnostics

:skip_update
echo.
echo Skipping auto-update. If you want to manually update PowerModeToggle.bat:
echo.
echo 1. Open PowerModeToggle.bat in Notepad
echo 2. Find the line: set "ULTIMATE_GUID=..."
echo 3. Replace with your GUID (if different from what's shown above)

:end_diagnostics
echo.
echo ============================================================
echo DIAGNOSTICS COMPLETE
echo ============================================================
echo.
echo Report generated: %date% %time%
echo.
echo NEXT STEPS:
echo 1. Review the power plans listed above
echo 2. If updated, test PowerModeToggle.bat by running it as Administrator
echo 3. For questions, see README.md
echo.
pause
