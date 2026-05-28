@echo off
:: Batch script to replace the entire application directory contents on Windows
:: Args:
:: %1: Process ID (PID) of the parent application to wait for
:: %2: Full path of the destination directory (dist\Camplife DataLoader)
:: %3: Full path of the temporary extracted directory
:: %4: Name of the executable to start (Camplife DataLoader.exe)

set PID=%~1
set DEST_DIR=%~2
set TEMP_DIR=%~3
set EXE_NAME=%~4

echo Checking process ID %PID%...

:wait_loop
tasklist /FI "PID eq %PID%" 2>NUL | find /I "%PID%" >NUL
if "%ERRORLEVEL%"=="0" (
    echo Waiting for application to exit...
    timeout /t 1 /nobreak >NUL
    goto wait_loop
)

echo Swapping files...
:: Clear out old internal files first to prevent stale resource conflicts
if exist "%DEST_DIR%\_internal" (
    rmdir /S /Q "%DEST_DIR%\_internal" >NUL
)

:: Copy everything over (including subdirectories, hidden/system, overwriting read-only)
xcopy /E /I /H /R /Y "%TEMP_DIR%" "%DEST_DIR%" >NUL
if errorlevel 1 (
    echo Copy failed, destination files may still be locked. Retrying in 2 seconds...
    timeout /t 2 /nobreak >NUL
    xcopy /E /I /H /R /Y "%TEMP_DIR%" "%DEST_DIR%" >NUL
)

echo Launching new version...
start "" "%DEST_DIR%\%EXE_NAME%"

echo Update complete.
exit
