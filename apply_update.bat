@echo off
:: Batch script to replace the running executable on Windows
:: Args:
:: %1: Process ID (PID) of the parent application to wait for
:: %2: Full path of the destination executable to replace
:: %3: Full path of the temporary downloaded new executable

set PID=%~1
set DEST=%~2
set TEMP=%~3

echo Checking process ID %PID%...

:wait_loop
tasklist /FI "PID eq %PID%" 2>NUL | find /I "%PID%" >NUL
if "%ERRORLEVEL%"=="0" (
    echo Waiting for application to exit...
    timeout /t 1 /nobreak >NUL
    goto wait_loop
)

echo Swapping executable...
:: Attempt to copy/replace
copy /Y "%TEMP%" "%DEST%" >NUL
if errorlevel 1 (
    echo Copy failed, destination may still be locked. Retrying in 2 seconds...
    timeout /t 2 /nobreak >NUL
    copy /Y "%TEMP%" "%DEST%" >NUL
)

echo Launching new version...
start "" "%DEST%"

echo Update complete.
exit
