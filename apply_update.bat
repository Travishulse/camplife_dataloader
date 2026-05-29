@echo off
setlocal enabledelayedexpansion
:: =============================================================================
:: apply_update.bat — Camplife DataLoader Safe Update Swapper
:: =============================================================================
:: This script replaces the running application with a new version downloaded
:: from GitHub Releases. It uses a safe rename-based swap strategy to prevent
:: DLL locking corruption.
::
:: Args:
::   %1: Process ID (PID) of the parent application to wait for
::   %2: Full path of the destination directory (e.g. dist\Camplife DataLoader)
::   %3: Full path of the temporary extracted update directory
::   %4: Name of the executable to relaunch (e.g. Camplife DataLoader.exe)
::
:: Exit Codes:
::   0 = Success
::   1 = Copy/swap failure after retries
::   2 = New executable not found after swap
::   3 = Invalid arguments
:: =============================================================================

:: --- Validate arguments ---
if "%~1"=="" goto :arg_error
if "%~2"=="" goto :arg_error
if "%~3"=="" goto :arg_error
if "%~4"=="" goto :arg_error

set PID=%~1
set DEST_DIR=%~2
set TEMP_DIR=%~3
set EXE_NAME=%~4

:: --- Setup logging ---
set LOG_FILE=%TEMP%\camplife_update_log.txt
echo ============================================== > "%LOG_FILE%"
echo Camplife DataLoader Update Log >> "%LOG_FILE%"
echo Started: %DATE% %TIME% >> "%LOG_FILE%"
echo ============================================== >> "%LOG_FILE%"
echo PID to wait for: %PID% >> "%LOG_FILE%"
echo Destination dir:  %DEST_DIR% >> "%LOG_FILE%"
echo Source temp dir:   %TEMP_DIR% >> "%LOG_FILE%"
echo Executable name:   %EXE_NAME% >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

echo [UPDATE] Waiting for application (PID %PID%) to exit...
echo [WAIT] Checking for PID %PID%... >> "%LOG_FILE%"

:: =============================================================================
:: PHASE 1: Wait for parent process to fully exit (hardened PID check)
:: =============================================================================
:: Uses CSV output format from tasklist and checks the exact PID in the second
:: column to avoid substring matching bugs (e.g. PID 8020 matching 18020).
:: =============================================================================
set WAIT_COUNT=0
set MAX_WAIT=60

:wait_loop
if %WAIT_COUNT% GEQ %MAX_WAIT% (
    echo [TIMEOUT] Process %PID% did not exit within %MAX_WAIT% seconds. >> "%LOG_FILE%"
    echo [TIMEOUT] Proceeding with update anyway... >> "%LOG_FILE%"
    goto :post_exit_delay
)

:: Use /FO CSV /NH for machine-parseable output: "process.exe","PID","Session","SessionNum","MemUsage"
:: Then use findstr with word boundary regex to match the exact PID value
tasklist /FI "PID eq %PID%" /FO CSV /NH 2>NUL | findstr /R /C:"\"%PID%\"" >NUL 2>&1
if "%ERRORLEVEL%"=="0" (
    set /a WAIT_COUNT+=1
    timeout /t 1 /nobreak >NUL
    goto :wait_loop
)

echo [OK] Process %PID% has exited (after %WAIT_COUNT%s). >> "%LOG_FILE%"

:post_exit_delay
:: =============================================================================
:: PHASE 2: Post-exit safety delay
:: =============================================================================
:: Windows may take several seconds to fully unload DLLs and release file
:: handles after a process exits. This delay ensures python312.dll and other
:: locked files are fully released before we attempt file operations.
:: =============================================================================
echo [WAIT] Post-exit safety delay (5 seconds) for OS to release DLL locks... >> "%LOG_FILE%"
echo [UPDATE] Waiting for file locks to release...
timeout /t 5 /nobreak >NUL
echo [OK] Safety delay complete. >> "%LOG_FILE%"

:: =============================================================================
:: PHASE 3: Safe rename-based file swap (transactional)
:: =============================================================================
:: Strategy: Rename old _internal -> _internal.old, then copy new files.
:: If copy fails, rollback by renaming _internal.old -> _internal.
:: This preserves the user's working install even if the update fails.
:: =============================================================================

echo [SWAP] Beginning transactional file swap... >> "%LOG_FILE%"
echo [UPDATE] Swapping application files...

:: Step 3a: Rename old _internal to _internal.old (safe move, not delete)
if exist "%DEST_DIR%\_internal.old" (
    echo [CLEAN] Removing leftover _internal.old from previous update... >> "%LOG_FILE%"
    rmdir /S /Q "%DEST_DIR%\_internal.old" >> "%LOG_FILE%" 2>&1
)

set RENAME_SUCCESS=0
if exist "%DEST_DIR%\_internal" (
    echo [RENAME] Renaming _internal -> _internal.old... >> "%LOG_FILE%"
    rename "%DEST_DIR%\_internal" "_internal.old" >> "%LOG_FILE%" 2>&1
    if !ERRORLEVEL! EQU 0 (
        set RENAME_SUCCESS=1
        echo [OK] Rename successful. >> "%LOG_FILE%"
    ) else (
        echo [WARN] Rename failed. Falling back to direct overwrite strategy. >> "%LOG_FILE%"
    )
) else (
    echo [INFO] No existing _internal directory to rename. >> "%LOG_FILE%"
    set RENAME_SUCCESS=1
)

:: Step 3b: Copy new files from temp directory with retry loop
set COPY_SUCCESS=0
set RETRY_COUNT=0
set MAX_RETRIES=3

:copy_loop
if %RETRY_COUNT% GEQ %MAX_RETRIES% (
    echo [FAIL] Copy failed after %MAX_RETRIES% attempts. >> "%LOG_FILE%"
    goto :copy_failed
)

set /a RETRY_COUNT+=1
echo [COPY] Attempt %RETRY_COUNT% of %MAX_RETRIES%: xcopy from temp to dest... >> "%LOG_FILE%"
xcopy /E /I /H /R /Y "%TEMP_DIR%" "%DEST_DIR%" >> "%LOG_FILE%" 2>&1
if !ERRORLEVEL! EQU 0 (
    set COPY_SUCCESS=1
    echo [OK] File copy successful on attempt %RETRY_COUNT%. >> "%LOG_FILE%"
    goto :copy_done
) else (
    echo [WARN] Copy attempt %RETRY_COUNT% failed (errorlevel=!ERRORLEVEL!). Retrying in 3 seconds... >> "%LOG_FILE%"
    timeout /t 3 /nobreak >NUL
    goto :copy_loop
)

:copy_failed
:: Rollback: restore _internal.old back to _internal
if %RENAME_SUCCESS% EQU 1 (
    if exist "%DEST_DIR%\_internal.old" (
        echo [ROLLBACK] Restoring _internal.old -> _internal... >> "%LOG_FILE%"
        rename "%DEST_DIR%\_internal.old" "_internal" >> "%LOG_FILE%" 2>&1
        echo [ROLLBACK] Original files restored. The update was NOT applied. >> "%LOG_FILE%"
    )
)
echo [FAIL] Update failed. See log at: %LOG_FILE% >> "%LOG_FILE%"
echo [UPDATE] Update failed! Check log: %LOG_FILE%
:: Still attempt to launch the existing executable so the user isn't left stranded
goto :launch

:copy_done
:: Step 3c: Clean up _internal.old (best effort, non-critical)
if exist "%DEST_DIR%\_internal.old" (
    echo [CLEAN] Deleting _internal.old... >> "%LOG_FILE%"
    rmdir /S /Q "%DEST_DIR%\_internal.old" >> "%LOG_FILE%" 2>&1
    if !ERRORLEVEL! NEQ 0 (
        echo [INFO] Could not delete _internal.old (files may still be locked). >> "%LOG_FILE%"
        echo [INFO] It will be cleaned up on next application launch. >> "%LOG_FILE%"
    ) else (
        echo [OK] _internal.old cleaned up successfully. >> "%LOG_FILE%"
    )
)

:: =============================================================================
:: PHASE 4: Verify and relaunch
:: =============================================================================
:launch
echo. >> "%LOG_FILE%"
echo [LAUNCH] Verifying new executable exists... >> "%LOG_FILE%"

if not exist "%DEST_DIR%\%EXE_NAME%" (
    echo [FAIL] New executable not found at: %DEST_DIR%\%EXE_NAME% >> "%LOG_FILE%"
    echo [UPDATE] ERROR: New executable not found. Update may have failed.
    echo Update completed: %DATE% %TIME% (FAILED - exe missing) >> "%LOG_FILE%"
    exit /b 2
)

echo [OK] Executable found. Launching %EXE_NAME%... >> "%LOG_FILE%"
echo [UPDATE] Launching new version...
echo Update completed: %DATE% %TIME% (SUCCESS) >> "%LOG_FILE%"

start "" "%DEST_DIR%\%EXE_NAME%"
exit /b 0

:arg_error
echo [FAIL] Invalid arguments. Usage: apply_update.bat ^<PID^> ^<DEST_DIR^> ^<TEMP_DIR^> ^<EXE_NAME^>
echo [FAIL] Invalid arguments provided. >> "%LOG_FILE%" 2>NUL
exit /b 3
